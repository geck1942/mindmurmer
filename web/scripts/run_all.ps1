Invoke-Item (start powershell ((Split-Path $MyInvocation.InvocationName) + "\run_osc.ps1"))
Invoke-Item (start powershell ((Split-Path $MyInvocation.InvocationName) + "\run_lights.ps1"))
Invoke-Item (start powershell ((Split-Path $MyInvocation.InvocationName) + "\run_fr0st.ps1"))
Invoke-Item (start powershell ((Split-Path $MyInvocation.InvocationName) + "\run_sound.ps1"))
# exit