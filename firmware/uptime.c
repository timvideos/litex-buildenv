#include <stdio.h>
#include <string.h>
#include <time.h>

#include <generated/csr.h>

#include "uptime.h"

#include "stdio_wrap.h"

static int uptime_seconds = 0;
void uptime_service(void)
{
	static int last_event;

	if(elapsed(&last_event, SYSTEM_CLOCK_FREQUENCY)) {
		uptime_seconds++;
	}
}

int uptime(void)
{
	return uptime_seconds;
}

void uptime_print(void)
{
	wprintf("uptime: %s\n", uptime_str());
}

const char* uptime_str(void)
{
	static char buffer[9];
	sprintf(buffer, "%02d:%02d:%02d",
		(uptime_seconds/3600)%24,
		(uptime_seconds/60)%60,
		uptime_seconds%60);
	return buffer;
}
