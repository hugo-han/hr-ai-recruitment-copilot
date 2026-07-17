param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath
)


Write-Host "================================="
Write-Host "生成 Claude Runtime Context"
Write-Host "================================="


# ===================================
# 基础路径
# ===================================

$ClaudeFile = Join-Path `
$ProjectPath "CLAUDE.md"


$ProjectName = Split-Path `
$ProjectPath `
-Leaf


$TemplateFile = Join-Path `
$ProjectPath ".factory\claude-template.md"



# ===================================
# 检查模板
# ===================================

if(!(Test-Path $TemplateFile))
{
    Write-Host "错误: 找不到 claude-template.md"
    exit 1
}



# ===================================
# 读取模板
# ===================================

$content = Get-Content `
$TemplateFile `
-Encoding utf8 `
-Raw



# ===================================
# 替换项目变量
# ===================================

$content = $content.Replace(
"{{PROJECT_NAME}}",
$ProjectName
)


$content = $content.Replace(
"{{PROJECT_DESCRIPTION}}",
"由 OPC AI Software Factory 创建的AI工程项目"
)


$content = $content.Replace(
"{{ISSUE_NUMBER}}",
"N/A"
)


$content = $content.Replace(
"{{FEATURE_NAME}}",
"N/A"
)



# ===================================
# 生成 CLAUDE.md
# ===================================

Set-Content `
$ClaudeFile `
$content `
-Encoding utf8



Write-Host ""
Write-Host "Claude Runtime Context 已生成:"
Write-Host $ClaudeFile


# ===================================
# 行数检查
# ===================================

$lineCount = (
Get-Content $ClaudeFile
).Count


Write-Host ""
Write-Host "CLAUDE.md 行数:"
Write-Host $lineCount


if($lineCount -gt 100)
{
    Write-Host ""
    Write-Host "警告: CLAUDE.md超过100行，请优化模板"
}

else
{
    Write-Host ""
    Write-Host "Context大小符合要求"
}
