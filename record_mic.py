import subprocess
import os

def record_user_audio(output_path, duration_seconds=3):
    ps_commands = f"""
$memberDefinition = @'
[DllImport("winmm.dll", EntryPoint="mciSendStringA", CharSet=CharSet.Ansi)]
public static extern int mciSendString(string lpstrCommand, System.Text.StringBuilder lpstrReturnString, int uReturnLength, IntPtr hwndCallback);
'@
$winaudio = Add-Type -MemberDefinition $memberDefinition -Name "WinAudio" -Namespace "WinMM" -PassThru
[void]$winaudio::mciSendString("open new type waveaudio alias recsound", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("record recsound", $null, 0, [System.IntPtr]::Zero)
Start-Sleep -Seconds {duration_seconds}
[void]$winaudio::mciSendString("save recsound {output_path}", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("close recsound", $null, 0, [System.IntPtr]::Zero)
"""
    res = subprocess.run(
        ["powershell", "-Command", ps_commands],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    return res

if __name__ == "__main__":
    print("Recording 3 seconds...")
    res = record_user_audio("test_mic_py.wav", 3)
    print("Done! File exists:", os.path.exists("test_mic_py.wav"))
    if os.path.exists("test_mic_py.wav"):
        print("Size:", os.path.getsize("test_mic_py.wav"))
