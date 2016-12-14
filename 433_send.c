/*
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.

 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.

 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <stdlib.h>
#include <stdio.h>
#include <wiringPi.h>

#define PULSE_LENGTH 189
#define DEFAULT_PIN 0

/* based on RCSwitch library for arduino.
 * protocol (to multiply by pulse length):
 * 0 : 1 high, 3 low
 * 1 : 3 high, 1 low
 *
 * we send the code 10 times due to low quality / high noise
 * often seen with low cost 433Mhz RF receiver
 */

void send_code(int code, int length)
{
	int i;
	int mask = 1 << (length - 1);

	for (i = 0; i < length ; i++) {
		if ((code & mask) != 0) {
			digitalWrite(DEFAULT_PIN, HIGH);
			delayMicroseconds(PULSE_LENGTH * 3);
			digitalWrite(DEFAULT_PIN, LOW);
			delayMicroseconds(PULSE_LENGTH * 1);
		} else {
			digitalWrite(DEFAULT_PIN, HIGH);
			delayMicroseconds(PULSE_LENGTH * 1);
			digitalWrite(DEFAULT_PIN, LOW);
			delayMicroseconds(PULSE_LENGTH * 3);
		}
		mask = mask >> 1;
	}

	/* end with a 0 */
	digitalWrite(DEFAULT_PIN, HIGH);
	delayMicroseconds(PULSE_LENGTH * 1);
	digitalWrite(DEFAULT_PIN, LOW);
	delayMicroseconds(PULSE_LENGTH * 3);
}

void main(int argc, char *argv[])
{
	int *table;
	int i, code, length;

	if (argc != 3) {
		printf("error in arguments. usage : 433_send <code> <binary length> \n");
		return;
	}

	code = atoi(argv[1]);
	length = atoi(argv[2]);

	if (wiringPiSetup () == -1) {
		return;
	}
	pinMode(DEFAULT_PIN, OUTPUT);

	for (i = 0; i < 9; i++) {
		send_code(code, length);
		delayMicroseconds(10000);
	}
}
