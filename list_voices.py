import subprocess
import base64

script = (
    "Add-Type -AssemblyName System.Speech; "
    "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    "$synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name + ' (' + $_.VoiceInfo.Culture.Name + ')' }"
)

encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
res = subprocess.run(['powershell', '-EncodedCommand', encoded], capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
