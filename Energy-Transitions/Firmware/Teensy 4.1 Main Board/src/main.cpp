#include <wav_trigger.h>

// Define audio tracks for ease of calling.
// (Can delete if not helpful).
#define READY_STATE 1
#define ERROR 2
#define PIECE_REGISTERED 3
#define PULL_SWITCH 4
#define FAIL 5
#define YELLOW 6
#define WIN 7
#define RESET 8

wavTrigger wavTrig;

void setup() {
    //Serial.begin(9600);

    // Wait for the WAV Trigger to finish power up & reset before trying to send commands.
    delay(1000);
    wavTrig.start();
    delay(10);

    // Send a stop-all command and reset the sample-rate offset, in case we have
    //  reset while the WAV Trigger was already playing.
    wavTrig.stopAllTracks();
    wavTrig.samplerateOffset(0);
    wavTrig.masterGain(0);
    wavTrig.setAmpPwr(true);
    wavTrig.setReporting(true);
}

void loop() {
    wavTrig.stopAllTracks();
    wavTrig.trackPlayPoly(READY_STATE);
    delay(2000);

    wavTrig.trackPlayPoly(ERROR);
    delay(2000);

    wavTrig.trackPlayPoly(PIECE_REGISTERED);
    delay(2000);

    wavTrig.trackPlayPoly(PULL_SWITCH);
    delay(2000);

    wavTrig.trackPlayPoly(FAIL);
    delay(2000);

    wavTrig.trackPlayPoly(YELLOW);
    delay(2000);

    wavTrig.trackPlayPoly(WIN);
    delay(2000);

    wavTrig.trackPlayPoly(RESET);
    delay(2000);
}