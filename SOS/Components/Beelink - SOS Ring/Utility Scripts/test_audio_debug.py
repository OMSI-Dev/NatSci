"""
Audio System Debug Test
Tests MPV audio controller with detailed feedback.
"""

import sys
import os
import time

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

from audio_access import AudioController

def test_audio_controller():
    """Test audio controller with debug output."""
    print("="*60)
    print("Audio Controller Debug Test")
    print("="*60)
    
    # Initialize controller
    print("\n[TEST] Initializing AudioController...")
    controller = AudioController(
        sos2_ip="10.10.51.98",
        sos2_user="sos",
        audio_path="/AuxShare/audio/mp3"
    )
    
    if not controller.is_initialized:
        print("\n[TEST] ✗ FAILED: Controller not initialized")
        return False
    
    print("\n[TEST] ✓ Controller initialized successfully")
    
    # Test 1: Get volume
    print("\n" + "="*60)
    print("[TEST] Getting current volume...")
    volume = controller.get_volume()
    if volume is not None:
        print(f"[TEST] ✓ Current volume: {volume}%")
    else:
        print("[TEST] ✗ Failed to get volume")
    
    # Test 2: Set volume
    print("\n" + "="*60)
    print("[TEST] Setting volume to 30...")
    if controller.set_volume(30):
        print("[TEST] ✓ Volume command sent")
        time.sleep(0.5)
        new_vol = controller.get_volume()
        if new_vol == 30:
            print(f"[TEST] ✓ Volume confirmed: {new_vol}%")
        else:
            print(f"[TEST] ⚠ Volume mismatch - expected 30, got {new_vol}")
    else:
        print("[TEST] ✗ Failed to set volume")
    
    # Test 3: Play test audio (you'll need a valid audio file)
    print("\n" + "="*60)
    print("[TEST] Attempting to play test audio...")
    print("[TEST] Enter filename to test (e.g., 'air_1.mp3') or press Enter to skip:")
    filename = input("[TEST] Filename: ").strip()
    
    if filename:
        print(f"[TEST] Playing {filename} with debug enabled...")
        success = controller.play_audio(filename, loop=False, debug=True)
        if success:
            print("[TEST] ✓ Play command accepted")
            print("[TEST] Audio should be playing now. Waiting 5 seconds...")
            time.sleep(5)
            
            # Stop audio
            print("\n[TEST] Stopping audio...")
            if controller.stop_audio():
                print("[TEST] ✓ Stop command accepted")
            else:
                print("[TEST] ✗ Stop command failed")
        else:
            print("[TEST] ✗ Play command failed")
    else:
        print("[TEST] Skipping audio playback test")
    
    # Test 4: Restore volume
    print("\n" + "="*60)
    print("[TEST] Restoring volume to 50...")
    controller.set_volume(50)
    
    # Cleanup
    print("\n" + "="*60)
    print("[TEST] Cleaning up...")
    controller.close()
    
    print("\n" + "="*60)
    print("[TEST] Test complete!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        test_audio_controller()
    except KeyboardInterrupt:
        print("\n[TEST] Interrupted by user")
    except Exception as e:
        print(f"\n[TEST] Error: {e}")
        import traceback
        traceback.print_exc()
