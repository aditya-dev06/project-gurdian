import subprocess
import base64
import urllib.parse

text = "こんにちは"
encoded_text = urllib.parse.quote(text)
url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ja&client=tw-ob&q={encoded_text}"

ps_cmd = (
    "$ProgressPreference = 'SilentlyContinue'; "
    "$wmp = New-Object -ComObject WMPlayer.OCX.7; "
    f"$wmp.URL = '{url}'; "
    "$wmp.controls.play(); "
    "while ($wmp.playState -ne 1 -and $wmp.playState -ne 10 -and $wmp.playState -ne 2) { Start-Sleep -Milliseconds 100 }"
)

encoded_cmd = base64.b64encode(ps_cmd.encode('utf-16-le')).decode('ascii')
creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0x08000000

print("Playing Japanese TTS using Windows Media Player COM object...")
res = subprocess.run(
    ["powershell", "-WindowStyle", "Hidden", "-EncodedCommand", encoded_cmd],
    capture_output=True,
    text=True,
    creationflags=creationflags
)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
print("RETURNCODE:", res.returncode)
