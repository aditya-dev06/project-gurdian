$memberDefinition = @'
[DllImport("winmm.dll", EntryPoint="mciSendStringA", CharSet=CharSet.Ansi)]
public static extern int mciSendString(string lpstrCommand, System.Text.StringBuilder lpstrReturnString, int uReturnLength, IntPtr hwndCallback);
'@

$winaudio = Add-Type -MemberDefinition $memberDefinition -Name "WinAudio" -Namespace "WinMM" -PassThru
[void]$winaudio::mciSendString("open new type waveaudio alias recsound", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("record recsound", $null, 0, [System.IntPtr]::Zero)
Write-Output "Recording started..."
Start-Sleep -Seconds 3
[void]$winaudio::mciSendString("save recsound test_mic.wav", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("close recsound", $null, 0, [System.IntPtr]::Zero)
Write-Output "Recording finished and saved as test_mic.wav."
