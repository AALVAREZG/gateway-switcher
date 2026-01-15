# PowerShell script to generate application icons
# Run this script on Windows with .NET installed

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

function Create-Icon {
    param (
        [string]$OutputPath,
        [System.Drawing.Color]$BackgroundColor,
        [string]$Text,
        [int]$Size = 256
    )

    $bitmap = New-Object System.Drawing.Bitmap($Size, $Size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    # Set high quality rendering
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

    # Draw background circle
    $brush = New-Object System.Drawing.SolidBrush($BackgroundColor)
    $graphics.FillEllipse($brush, 10, 10, $Size - 20, $Size - 20)

    # Draw text
    $font = New-Object System.Drawing.Font("Segoe UI", [int]($Size * 0.35), [System.Drawing.FontStyle]::Bold)
    $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
    $textSize = $graphics.MeasureString($Text, $font)
    $x = ($Size - $textSize.Width) / 2
    $y = ($Size - $textSize.Height) / 2
    $graphics.DrawString($Text, $font, $textBrush, $x, $y)

    # Save as icon
    $icon = [System.Drawing.Icon]::FromHandle($bitmap.GetHicon())
    $stream = [System.IO.File]::Create($OutputPath)
    $icon.Save($stream)
    $stream.Close()

    # Cleanup
    $graphics.Dispose()
    $bitmap.Dispose()
    $brush.Dispose()
    $textBrush.Dispose()
    $font.Dispose()

    Write-Host "Created icon: $OutputPath"
}

# Create main app icon (blue)
Create-Icon -OutputPath "app.ico" -BackgroundColor ([System.Drawing.Color]::FromArgb(33, 150, 243)) -Text "GS"

# Create connected icon (green)
Create-Icon -OutputPath "connected.ico" -BackgroundColor ([System.Drawing.Color]::FromArgb(76, 175, 80)) -Text "GS"

# Create disconnected icon (red)
Create-Icon -OutputPath "disconnected.ico" -BackgroundColor ([System.Drawing.Color]::FromArgb(244, 67, 54)) -Text "GS"

Write-Host "`nIcons created successfully!"
Write-Host "Move these files to your GatewaySwitcher/Resources folder."
