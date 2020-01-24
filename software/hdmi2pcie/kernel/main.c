/*
 * HDMI2PCIe driver
 *
 * Copyright (C) 2018 / LambdaConcept / ramtin@lambdaconcept.com
 * Copyright (C) 2018 / LambdaConcept / po@lambdaconcept.com
 * Copyright (C) 2018 / EnjoyDigital  / florent@enjoy-digital.fr
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.

 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/types.h>
#include <linux/ioctl.h>
#include <linux/init.h>
#include <linux/mutex.h>
#include <linux/pci.h>
#include <linux/pci_regs.h>
#include <linux/v4l2-dv-timings.h>
#include <media/v4l2-device.h>
#include <media/v4l2-dev.h>
#include <media/v4l2-ioctl.h>
#include <media/v4l2-dv-timings.h>
#include <media/v4l2-ctrls.h>
#include <media/v4l2-event.h>
#include <media/videobuf2-v4l2.h>
#include <media/videobuf2-dma-contig.h>

#define HDMI2PCIE_NAME "HDMI2PCIe"

#define PCIE_FPGA_VENDOR_ID 0x10ee
#define PCIE_FPGA_DEVICE_ID 0x7022

#define HDMI2PCIE_DIR_IN 0
#define HDMI2PCIE_DIR_OUT 1

#define PCIE_BUF_SIZE 0x400000
#define READ_BUF_OFF (7*PCIE_BUF_SIZE)

struct hdmi2pcie_priv_data;

struct vid_channel {
	uint8_t dir;
	uint32_t sequence;
	struct hdmi2pcie_priv_data *common;

	struct v4l2_device v4l2_dev;
	struct video_device vdev;
	struct mutex lock;

	struct v4l2_dv_timings timings;
	struct v4l2_pix_format format;

	unsigned int *fb_idx;

	spinlock_t qlock;
	struct vb2_queue queue;
	struct list_head buf_list;
};

struct hdmi2pcie_priv_data {
	struct pci_dev *pdev;
	struct vid_channel *channels;
	uint8_t chan_cnt;
	/* PCIe BAR0 */
	resource_size_t bar0_size;
	phys_addr_t bar0_phys_addr;
	uint8_t *bar0_addr; /* virtual address of BAR0 */
};

static const struct v4l2_dv_timings_cap hdmi2pcie_timings_cap = {
	.type = V4L2_DV_BT_656_1120,
	.reserved = { 0 },
	V4L2_INIT_BT_TIMINGS(
		640, 1920,
		480, 1080,
		25000000, 148500000,
		V4L2_DV_BT_STD_CEA861,
		V4L2_DV_BT_CAP_PROGRESSIVE
	)
};

struct hdmi2pcie_buffer {
	struct vb2_v4l2_buffer vb;
	struct list_head list;
};

static inline struct hdmi2pcie_buffer *to_hdmi2pcie_buffer(struct vb2_buffer *vb2)
{
	return container_of(vb2, struct hdmi2pcie_buffer, vb);
}

static int queue_setup(struct vb2_queue *vq,
		       unsigned int *nbuffers, unsigned int *nplanes,
		       unsigned int sizes[], struct device *alloc_devs[])
{
	struct vid_channel *chan = vb2_get_drv_priv(vq);

	if (vq->num_buffers + *nbuffers < 3)
		*nbuffers = 3 - vq->num_buffers;

	if (*nplanes)
		return sizes[0] < chan->format.sizeimage ? -EINVAL : 0;

	*nplanes = 1;
	sizes[0] = chan->format.sizeimage;
	return 0;
}

static int buffer_prepare(struct vb2_buffer *vb)
{
	struct vid_channel *chan = vb2_get_drv_priv(vb->vb2_queue);
	unsigned long size = chan->format.sizeimage;

	if (vb2_plane_size(vb, 0) < size) {
		dev_err(&chan->common->pdev->dev, "buffer too small (%lu < %lu)\n",
			 vb2_plane_size(vb, 0), size);
		return -EINVAL;
	}

	vb2_set_plane_payload(vb, 0, size);
	return 0;
}

static void buffer_queue(struct vb2_buffer *vb)
{
	struct vid_channel *chan = vb2_get_drv_priv(vb->vb2_queue);
	//struct hdmi2pcie_buffer *hbuf = to_hdmi2pcie_buffer(vb);
	struct vb2_v4l2_buffer *vbuf = to_vb2_v4l2_buffer(vb);
	unsigned long size = vb2_get_plane_payload(vb, 0);
	void *buf = vb2_plane_vaddr(vb, 0);
	unsigned long flags;
	unsigned long fb_idx = (readl(chan->fb_idx) + 1) % 4;

	spin_lock_irqsave(&chan->qlock, flags);
	//list_add_tail(&hbuf->list, &priv->buf_list);
	if (chan->dir == HDMI2PCIE_DIR_IN)
		memcpy_fromio(buf, chan->common->bar0_addr + READ_BUF_OFF, size);
	else
		memcpy_toio(chan->common->bar0_addr + fb_idx * PCIE_BUF_SIZE, buf, size);

	writel(fb_idx, chan->fb_idx);

	vb->timestamp = ktime_get_ns();
	vbuf->sequence = chan->sequence++;
	vbuf->field = V4L2_FIELD_NONE;

	vb2_buffer_done(vb, VB2_BUF_STATE_DONE);

	spin_unlock_irqrestore(&chan->qlock, flags);
}

static void return_all_buffers(struct vid_channel *chan,
			       enum vb2_buffer_state state)
{
	struct hdmi2pcie_buffer *buf, *node;
	unsigned long flags;

	spin_lock_irqsave(&chan->qlock, flags);
	list_for_each_entry_safe(buf, node, &chan->buf_list, list) {
		vb2_buffer_done(&buf->vb.vb2_buf, state);
		list_del(&buf->list);
	}
	spin_unlock_irqrestore(&chan->qlock, flags);
}

static int start_streaming(struct vb2_queue *vq, unsigned int count)
{
	struct vid_channel *chan = vb2_get_drv_priv(vq);
	int ret = 0;

	chan->sequence = 0;

	//TODO: Start DMA

	if (ret) {
		return_all_buffers(chan, VB2_BUF_STATE_QUEUED);
	}
	return ret;
}

static void stop_streaming(struct vb2_queue *vq)
{
	struct vid_channel *chan = vb2_get_drv_priv(vq);

	return_all_buffers(chan, VB2_BUF_STATE_ERROR);
}

static struct vb2_ops hdmi2pcie_qops = {
	.queue_setup		= queue_setup,
	.buf_prepare		= buffer_prepare,
	.buf_queue		= buffer_queue,
	.start_streaming	= start_streaming,
	.stop_streaming		= stop_streaming,
	.wait_prepare		= vb2_ops_wait_prepare,
	.wait_finish		= vb2_ops_wait_finish,
};

static int hdmi2pcie_querycap(struct file *file, void *private,
			     struct v4l2_capability *cap)
{
	struct vid_channel *chan = video_drvdata(file);

	strlcpy(cap->driver, KBUILD_MODNAME, sizeof(cap->driver));
	strlcpy(cap->card, "HDMI2PCIe", sizeof(cap->card));
	snprintf(cap->bus_info, sizeof(cap->bus_info), "PCI:%s",
		 pci_name(chan->common->pdev));
	return 0;
}

static void hdmi2pcie_fill_pix_format(struct vid_channel *chan,
				     struct v4l2_pix_format *pix)
{
	pix->pixelformat = V4L2_PIX_FMT_UYVY;
	pix->width = chan->timings.bt.width;
	pix->height = chan->timings.bt.height;
	if (chan->timings.bt.interlaced) {
		pix->field = V4L2_FIELD_ALTERNATE;
		pix->height /= 2;
	} else {
		pix->field = V4L2_FIELD_NONE;
	}
	pix->colorspace = V4L2_COLORSPACE_REC709;

	pix->bytesperline = pix->width * 2;
	pix->sizeimage = pix->bytesperline * pix->height;
	pix->priv = 0;
}

static int hdmi2pcie_try_fmt_vid(struct file *file, void *private,
				    struct v4l2_format *f)
{
	struct vid_channel *chan = video_drvdata(file);
	struct v4l2_pix_format *pix = &f->fmt.pix;

	if (pix->pixelformat != V4L2_PIX_FMT_UYVY) {
		dev_info(&chan->common->pdev->dev, "%s: wrong format\n", __PRETTY_FUNCTION__);
	}
	hdmi2pcie_fill_pix_format(chan, pix);
	return 0;
}

static int hdmi2pcie_s_fmt_vid(struct file *file, void *private,
				  struct v4l2_format *f)
{
	struct vid_channel *chan = video_drvdata(file);
	int ret;

	ret = hdmi2pcie_try_fmt_vid(file, private, f);
	if (ret)
		return ret;

	if (vb2_is_busy(&chan->queue))
		return -EBUSY;

	// TODO: set format on the device
	chan->format = f->fmt.pix;
	return 0;
}

static int hdmi2pcie_g_fmt_vid(struct file *file, void *private,
				  struct v4l2_format *f)
{
	struct vid_channel *chan = video_drvdata(file);

	f->fmt.pix = chan->format;
	return 0;
}

static int hdmi2pcie_enum_fmt_vid(struct file *file, void *private,
				     struct v4l2_fmtdesc *f)
{
	if (f->index > 0)
		return -EINVAL;

	f->pixelformat = V4L2_PIX_FMT_UYVY;
	return 0;
}

static int hdmi2pcie_s_dv_timings(struct file *file, void *_fh,
				 struct v4l2_dv_timings *timings)
{
	struct vid_channel *chan = video_drvdata(file);

	if (!v4l2_valid_dv_timings(timings, &hdmi2pcie_timings_cap, NULL, NULL))
		return -EINVAL;

	if (!v4l2_find_dv_timings_cap(timings, &hdmi2pcie_timings_cap,
				      0, NULL, NULL))
		return -EINVAL;

	if (v4l2_match_dv_timings(timings, &chan->timings, 0, false))
		return 0;

	if (vb2_is_busy(&chan->queue))
		return -EBUSY;

	chan->timings = *timings;

	hdmi2pcie_fill_pix_format(chan, &chan->format);
	return 0;
}

static int hdmi2pcie_g_dv_timings(struct file *file, void *_fh,
				 struct v4l2_dv_timings *timings)
{
	struct vid_channel *chan = video_drvdata(file);

	*timings = chan->timings;
	return 0;
}

static int hdmi2pcie_enum_dv_timings(struct file *file, void *_fh,
				    struct v4l2_enum_dv_timings *timings)
{
	return v4l2_enum_dv_timings_cap(timings, &hdmi2pcie_timings_cap,
					NULL, NULL);
}

static int hdmi2pcie_query_dv_timings(struct file *file, void *_fh,
				     struct v4l2_dv_timings *timings)
{
	// TODO: detect current timings/signal state (out of range, disconnected, ...)

	return 0;
}

static int hdmi2pcie_dv_timings_cap(struct file *file, void *fh,
				   struct v4l2_dv_timings_cap *cap)
{
	*cap = hdmi2pcie_timings_cap;
	return 0;
}

static int hdmi2pcie_enum_input(struct file *file, void *private,
			       struct v4l2_input *i)
{
	if (i->index > 0)
		return -EINVAL;

	i->type = V4L2_INPUT_TYPE_CAMERA;
	strlcpy(i->name, "HDMI In", sizeof(i->name));
	i->capabilities = V4L2_IN_CAP_DV_TIMINGS;
	return 0;
}

static int hdmi2pcie_s_input(struct file *file, void *private, unsigned int i)
{
	struct vid_channel *chan = video_drvdata(file);

	if (i > 0)
		return -EINVAL;

	if (vb2_is_busy(&chan->queue))
		return -EBUSY;

	chan->vdev.tvnorms = 0;

	hdmi2pcie_fill_pix_format(chan, &chan->format);
	return 0;
}

static int hdmi2pcie_g_input(struct file *file, void *private, unsigned int *i)
{
	*i = 0;
	return 0;
}

static int hdmi2pcie_enum_output(struct file *file, void *private,
			       struct v4l2_output *i)
{
	if (i->index > 0)
		return -EINVAL;

	i->type = V4L2_OUTPUT_TYPE_ANALOG;
	strlcpy(i->name, "HDMI Out", sizeof(i->name));
	i->capabilities = V4L2_OUT_CAP_DV_TIMINGS;
	return 0;
}

static int hdmi2pcie_s_output(struct file *file, void *private, unsigned int i)
{
	struct vid_channel *chan = video_drvdata(file);

	if (i > 0)
		return -EINVAL;

	if (vb2_is_busy(&chan->queue))
		return -EBUSY;

	chan->vdev.tvnorms = 0;

	hdmi2pcie_fill_pix_format(chan, &chan->format);
	return 0;
}

static int hdmi2pcie_g_output(struct file *file, void *private, unsigned int *i)
{
	*i = 0;
	return 0;
}

static const struct v4l2_ioctl_ops hdmi2pcie_ioctl_in_ops = {
	.vidioc_querycap = hdmi2pcie_querycap,

	.vidioc_try_fmt_vid_cap = hdmi2pcie_try_fmt_vid,
	.vidioc_s_fmt_vid_cap = hdmi2pcie_s_fmt_vid,
	.vidioc_g_fmt_vid_cap = hdmi2pcie_g_fmt_vid,
	.vidioc_enum_fmt_vid_cap = hdmi2pcie_enum_fmt_vid,

	.vidioc_s_dv_timings = hdmi2pcie_s_dv_timings,
	.vidioc_g_dv_timings = hdmi2pcie_g_dv_timings,
	.vidioc_enum_dv_timings = hdmi2pcie_enum_dv_timings,
	.vidioc_query_dv_timings = hdmi2pcie_query_dv_timings,
	.vidioc_dv_timings_cap = hdmi2pcie_dv_timings_cap,

	.vidioc_enum_input = hdmi2pcie_enum_input,
	.vidioc_g_input = hdmi2pcie_g_input,
	.vidioc_s_input = hdmi2pcie_s_input,

	.vidioc_reqbufs = vb2_ioctl_reqbufs,
	.vidioc_create_bufs = vb2_ioctl_create_bufs,
	.vidioc_querybuf = vb2_ioctl_querybuf,
	.vidioc_qbuf = vb2_ioctl_qbuf,
	.vidioc_dqbuf = vb2_ioctl_dqbuf,
	.vidioc_expbuf = vb2_ioctl_expbuf,
	.vidioc_streamon = vb2_ioctl_streamon,
	.vidioc_streamoff = vb2_ioctl_streamoff,

	.vidioc_log_status = v4l2_ctrl_log_status,
	.vidioc_subscribe_event = v4l2_ctrl_subscribe_event,
	.vidioc_unsubscribe_event = v4l2_event_unsubscribe,
};

static const struct v4l2_ioctl_ops hdmi2pcie_ioctl_out_ops = {
	.vidioc_querycap = hdmi2pcie_querycap,

	.vidioc_try_fmt_vid_out = hdmi2pcie_try_fmt_vid,
	.vidioc_s_fmt_vid_out = hdmi2pcie_s_fmt_vid,
	.vidioc_g_fmt_vid_out = hdmi2pcie_g_fmt_vid,
	.vidioc_enum_fmt_vid_out = hdmi2pcie_enum_fmt_vid,

	.vidioc_s_dv_timings = hdmi2pcie_s_dv_timings,
	.vidioc_g_dv_timings = hdmi2pcie_g_dv_timings,
	.vidioc_enum_dv_timings = hdmi2pcie_enum_dv_timings,
	.vidioc_query_dv_timings = hdmi2pcie_query_dv_timings,
	.vidioc_dv_timings_cap = hdmi2pcie_dv_timings_cap,

	.vidioc_enum_output = hdmi2pcie_enum_output,
	.vidioc_g_output = hdmi2pcie_g_output,
	.vidioc_s_output = hdmi2pcie_s_output,

	.vidioc_reqbufs = vb2_ioctl_reqbufs,
	.vidioc_create_bufs = vb2_ioctl_create_bufs,
	.vidioc_querybuf = vb2_ioctl_querybuf,
	.vidioc_qbuf = vb2_ioctl_qbuf,
	.vidioc_dqbuf = vb2_ioctl_dqbuf,
	.vidioc_expbuf = vb2_ioctl_expbuf,
	.vidioc_streamon = vb2_ioctl_streamon,
	.vidioc_streamoff = vb2_ioctl_streamoff,

	.vidioc_log_status = v4l2_ctrl_log_status,
	.vidioc_subscribe_event = v4l2_ctrl_subscribe_event,
	.vidioc_unsubscribe_event = v4l2_event_unsubscribe,
};

static const struct v4l2_file_operations hdmi2pcie_fops = {
	.owner = THIS_MODULE,
	.open = v4l2_fh_open,
	.release = vb2_fop_release,
	.unlocked_ioctl = video_ioctl2,
	.read = vb2_fop_read,
	.mmap = vb2_fop_mmap,
	.poll = vb2_fop_poll,
};

static int hdmi2pcie_register_video_dev(struct pci_dev *pdev, struct vid_channel *chan, uint8_t dir)
{
	static const struct v4l2_dv_timings timings_def = V4L2_DV_BT_CEA_1920X1080P60;
	struct video_device *vdev = &chan->vdev;
	struct vb2_queue *q = &chan->queue;
	int ret;

	chan->dir = dir;

	ret = v4l2_device_register(&pdev->dev, &chan->v4l2_dev);
	if (ret) {
		dev_err(&pdev->dev, "v4l2_device_register failed, ret=%d\n", ret);
		return ret;
	}

	// Last 4 bytes of buffer area contain the buffer index used for synchronization with FPGA firmware
	if (dir == HDMI2PCIE_DIR_IN)
		chan->fb_idx = (unsigned int*)(chan->common->bar0_addr + 8*PCIE_BUF_SIZE - sizeof(unsigned int));
	else
		chan->fb_idx = (unsigned int*)(chan->common->bar0_addr + 4*PCIE_BUF_SIZE - sizeof(unsigned int));

	writel(0, chan->fb_idx);

	mutex_init(&chan->lock);

	q->io_modes = VB2_MMAP | VB2_DMABUF;
	q->dev = &pdev->dev;
	q->drv_priv = chan;
	q->buf_struct_size = sizeof(struct hdmi2pcie_buffer);
	q->ops = &hdmi2pcie_qops;
	q->mem_ops = &vb2_dma_contig_memops;
	q->timestamp_flags = V4L2_BUF_FLAG_TIMESTAMP_MONOTONIC;
	q->min_buffers_needed = 2;
	q->lock = &chan->lock;
	q->gfp_flags = GFP_DMA32;

	if (dir == HDMI2PCIE_DIR_IN) {
		q->io_modes |= VB2_READ;
		q->type = V4L2_BUF_TYPE_VIDEO_CAPTURE; 
	} else {
		q->io_modes |= VB2_WRITE;
		q->type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
	}

	ret = vb2_queue_init(q);
	if (ret) {
		dev_err(&pdev->dev, "vb2_queue_init failed, ret=%d\n", ret);
		goto v4l2_unregister;
	}

	INIT_LIST_HEAD(&chan->buf_list);
	spin_lock_init(&chan->qlock);

	strlcpy(vdev->name, HDMI2PCIE_NAME, sizeof(vdev->name));
	vdev->release = video_device_release_empty;

	vdev->fops = &hdmi2pcie_fops;
	vdev->device_caps = V4L2_CAP_READWRITE | V4L2_CAP_STREAMING;

	if (dir == HDMI2PCIE_DIR_IN) {
		vdev->ioctl_ops = &hdmi2pcie_ioctl_in_ops;
		vdev->device_caps |= V4L2_CAP_VIDEO_CAPTURE;
	} else {
		vdev->ioctl_ops = &hdmi2pcie_ioctl_out_ops;
		vdev->device_caps |= V4L2_CAP_VIDEO_OUTPUT;
	}	


	vdev->lock = &chan->lock;
	vdev->queue = q;
	vdev->vfl_dir = dir ? VFL_DIR_TX : VFL_DIR_RX;
	vdev->v4l2_dev = &chan->v4l2_dev;
	video_set_drvdata(vdev, chan);

	ret = video_register_device(vdev, VFL_TYPE_GRABBER, -1);
	if (ret) {
		dev_err(&pdev->dev, "video_register_device failed, ret=%d\n", ret);
		goto v4l2_unregister;
	}

	chan->timings = timings_def;

	dev_info(&pdev->dev, "V4L2 HDMI2PCIe driver loaded");
	return 0;

v4l2_unregister:
	v4l2_device_unregister(&chan->v4l2_dev);
	return ret;
}

static int hdmi2pcie_pci_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
	int i;
	int ret;
	uint8_t rev_id;

	struct device *dev = &pdev->dev;
	struct hdmi2pcie_priv_data *priv;

	dev_info(dev, "\e[1m[Probing device]\e[0m\n");

	priv = kzalloc(sizeof(*priv), GFP_KERNEL);
	priv->chan_cnt = 2;
	if(!priv) {
		dev_err(dev, "Cannot allocate memory\n");
		ret = -ENOMEM;
		goto fail_before_pci_device_enable;
	}
	priv->channels = kzalloc(sizeof(*priv->channels) * priv->chan_cnt, GFP_KERNEL);
	if(!priv->channels) {
		dev_err(dev, "Cannot allocate memory\n");
		ret = -ENOMEM;
		goto fail_before_pci_device_enable;
	}

	for (i = 0; i < priv->chan_cnt; i++)
		priv->channels[i].common = priv;

	pci_set_drvdata(pdev, priv);
	priv->pdev = pdev;

	ret = pci_enable_device(pdev);
	if (ret != 0) {
		dev_err(dev, "Cannot enable device\n");
		goto fail_before_pci_device_enable;
	}

	/* check device version */
	pci_read_config_byte(pdev, PCI_REVISION_ID, &rev_id);
	if (rev_id != 1) {
		dev_err(dev, "Unsupported device version %d\n", rev_id);
		goto fail_before_pci_request_regions;
	}

	if (pci_request_regions(pdev, HDMI2PCIE_NAME) < 0) {
		dev_err(dev, "Could not request regions\n");
		goto fail_before_pci_request_regions;
	}

	/* check bar0 config */
	if (!(pci_resource_flags(pdev, 0) & IORESOURCE_MEM)) {
		dev_err(dev, "Invalid BAR0 configuration\n");
		goto fail_before_bar_remap;
	}

	priv->bar0_addr = pci_ioremap_bar(pdev, 0);
	priv->bar0_size = pci_resource_len(pdev, 0);
	priv->bar0_phys_addr = pci_resource_start(pdev, 0);
	if (!priv->bar0_addr) {
		dev_err(dev, "Could not map BAR0\n");
		goto fail_before_bar_remap;
	}

	pci_set_master(pdev);
	ret = pci_set_dma_mask(pdev, DMA_BIT_MASK(32));
	if (ret) {
		dev_err(dev, "Failed to set DMA mask\n");
		goto fail_before_pci_msi_enable;
	};

	ret = pci_enable_msi(pdev);
	if (ret) {
		dev_err(dev, "Failed to enable MSI\n");
		goto fail_before_pci_msi_enable;
	}

	// TODO: in total we should register 2 input and 2 output channels, one for each HDMI port

	ret = hdmi2pcie_register_video_dev(pdev, &priv->channels[0], HDMI2PCIE_DIR_IN);
	ret += hdmi2pcie_register_video_dev(pdev, &priv->channels[1], HDMI2PCIE_DIR_OUT);
	if (ret) {
		dev_err(dev, "Failed to register V4L2 device");
		goto fail_before_register_video_dev;
	}

	return 0;

fail_before_register_video_dev:
	pci_disable_msi(pdev);
fail_before_pci_msi_enable:
	pci_iounmap(pdev, priv->bar0_addr);
fail_before_bar_remap:
	pci_release_regions(pdev);
fail_before_pci_request_regions:
	pci_disable_device(pdev);
fail_before_pci_device_enable:
	if(priv){
		if(priv->channels)
			kfree(priv->channels);
		kfree(priv);
	}
	return ret;
}

static void hdmi2pcie_pci_remove(struct pci_dev *pdev)
{
	struct hdmi2pcie_priv_data *priv;
	int i;

	priv = pci_get_drvdata(pdev);

	dev_info(&pdev->dev, "\e[1m[Removing device]\e[0m\n");

	pci_disable_msi(pdev);

	if(priv)
		pci_iounmap(pdev, priv->bar0_addr);

	for (i = 0; i < priv->chan_cnt; i++) {
		video_unregister_device(&priv->channels[i].vdev);
		v4l2_device_unregister(&priv->channels[i].v4l2_dev);
	}

	if(priv){
		if(priv->channels)
			kfree(priv->channels);
		kfree(priv);
	}

	pci_disable_device(pdev);
	pci_release_regions(pdev);
}

static const struct pci_device_id hdmi2pcie_pci_ids[] = {
	{ PCI_DEVICE(PCIE_FPGA_VENDOR_ID, PCIE_FPGA_DEVICE_ID ), },
	{ 0, }
};
MODULE_DEVICE_TABLE(pci, hdmi2pcie_pci_ids);

static struct pci_driver hdmi2pcie_pci_driver = {
	.name = HDMI2PCIE_NAME,
	.id_table = hdmi2pcie_pci_ids,
	.probe = hdmi2pcie_pci_probe,
	.remove = hdmi2pcie_pci_remove,
};

static int __init hdmi2pcie_module_init(void)
{
	int ret;

	ret = pci_register_driver(&hdmi2pcie_pci_driver);
	if (ret < 0) {
		printk(KERN_ERR HDMI2PCIE_NAME " Error while registering PCI driver\n");
		return ret;
	}

	return 0;
}

static void __exit hdmi2pcie_module_exit(void)
{
	pci_unregister_driver(&hdmi2pcie_pci_driver);
}


module_init(hdmi2pcie_module_init);
module_exit(hdmi2pcie_module_exit);

MODULE_LICENSE("GPL");
