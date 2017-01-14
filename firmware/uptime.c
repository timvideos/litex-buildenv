#include <stdio.h>
#include <string.h>
#include <time.h>

#include <generated/csr.h>

#include "uptime.h"

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
	printf(uptime_str());
	printf("\n\r");
}

const char* uptime_str(void)
{
	static char buffer[16];
	sprintf(buffer, "uptime %02d:%02d:%02d",
		(uptime_seconds/3600)%24,
		(uptime_seconds/60)%60,
		uptime_seconds%60);
	return buffer;
}
