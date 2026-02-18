#include <wavTrigger.h>

wavTrigger wTrig;

void setupAudio()
{
    // If the Arduino is powering the WAV Trigger, we should wait for the WAV
    //  Trigger to finish reset before trying to send commands.
    delay(1000);

    // WAV Trigger startup at 57600
    wTrig.start();
    delay(10);

    // Send a stop-all command and reset the sample-rate offset, in case we have
    //  reset while the WAV Trigger was already playing.
    wTrig.stopAllTracks();
    wTrig.samplerateOffset(0);
}

void playTubeComplete()
{
    wTrig.samplerateOffset(0);
    wTrig.masterGain(0); // Reset the master gain to 0dB

    wTrig.trackGain(1, -40);       // Preset Track 1 gain to -40dB
    wTrig.trackPlayPoly(1);        // Start Track 1
    wTrig.trackFade(1, 0, 500, 0); // Fade Track 1 up to 0dB over 0.5 secs

    // Fade out?
}

void playGameComplete()
{
    wTrig.samplerateOffset(0);
    wTrig.masterGain(0); // Reset the master gain to 0dB

    wTrig.trackGain(2, -40);       // Preset Track 2 gain to -40dB
    wTrig.trackPlayPoly(2);        // Start Track 2
    wTrig.trackFade(2, 0, 500, 0); // Fade Track 2 up to 0dB over 0.5 secs

    // Fade out?
}