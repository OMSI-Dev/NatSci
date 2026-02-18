#include <audio/Tsunami.h>
Tsunami audioOut;

void startAudioPlayer()
{
  // uses serial1 adjusted in tsunami.h
  // if you are getting errors on build, comment out the softwareSerial include.
  audioOut.start();
  delay(1000); // start tsunami and wait for it to connect
  // reset incase we are out of sync on boot
  audioOut.stopAllTracks();
  audioOut.samplerateOffset(0, 0);
}

void turnOffAudio()
{
  audioOut.stopAllTracks();
}

/**
 * @param track  what audio track to play
 * @param channel what audio channel to play. 0-4
 */
void playAudio(uint8_t track, uint8_t channel)
{
  // plat track 1 on ch1
  audioOut.trackPlayPoly(track, channel, 0);
}

void stopAudioTrack(uint8_t track)
{
  audioOut.trackStop(track);
}