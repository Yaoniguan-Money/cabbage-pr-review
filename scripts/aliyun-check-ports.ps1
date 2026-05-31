# Check ECS security group ports from Windows (replace TargetHost with your public IP)
param(
    [string]$TargetHost = "47.96.155.7"
)

$ports = @(22, 8080, 80, 443)
foreach ($p in $ports) {
    $r = Test-NetConnection -ComputerName $TargetHost -Port $p -WarningAction SilentlyContinue
    $ok = $r.TcpTestSucceeded
    $status = if ($ok) { "open" } else { "closed (check security group / service)" }
    Write-Host ("port {0,-5} -> {1}" -f $p, $status)
}
