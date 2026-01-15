using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace GatewaySwitcher.Helpers
{
    /// <summary>
    /// Helper class for generating and managing application icons
    /// </summary>
    public static class IconHelper
    {
        [DllImport("user32.dll", CharSet = CharSet.Auto)]
        private static extern bool DestroyIcon(IntPtr handle);

        /// <summary>
        /// Creates a simple application icon with text
        /// </summary>
        public static Icon CreateIcon(string text, System.Drawing.Color backgroundColor, int size = 32)
        {
            using var bitmap = new Bitmap(size, size);
            using var graphics = Graphics.FromImage(bitmap);

            graphics.SmoothingMode = SmoothingMode.AntiAlias;
            graphics.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;

            // Draw background circle
            using (var brush = new SolidBrush(backgroundColor))
            {
                graphics.FillEllipse(brush, 1, 1, size - 2, size - 2);
            }

            // Draw text
            using (var font = new Font("Segoe UI", size * 0.35f, System.Drawing.FontStyle.Bold))
            using (var textBrush = new SolidBrush(System.Drawing.Color.White))
            {
                var textSize = graphics.MeasureString(text, font);
                float x = (size - textSize.Width) / 2;
                float y = (size - textSize.Height) / 2;
                graphics.DrawString(text, font, textBrush, x, y);
            }

            IntPtr hIcon = bitmap.GetHicon();
            return Icon.FromHandle(hIcon);
        }

        /// <summary>
        /// Creates the main application icon
        /// </summary>
        public static Icon CreateAppIcon(int size = 32)
        {
            return CreateIcon("GS", System.Drawing.Color.FromArgb(33, 150, 243), size);
        }

        /// <summary>
        /// Creates a connected status icon
        /// </summary>
        public static Icon CreateConnectedIcon(int size = 32)
        {
            return CreateIcon("GS", System.Drawing.Color.FromArgb(76, 175, 80), size);
        }

        /// <summary>
        /// Creates a disconnected status icon
        /// </summary>
        public static Icon CreateDisconnectedIcon(int size = 32)
        {
            return CreateIcon("GS", System.Drawing.Color.FromArgb(244, 67, 54), size);
        }

        /// <summary>
        /// Converts an Icon to an ImageSource for WPF
        /// </summary>
        public static ImageSource ToImageSource(this Icon icon)
        {
            var bitmap = icon.ToBitmap();
            var hBitmap = bitmap.GetHbitmap();

            ImageSource wpfBitmap = Imaging.CreateBitmapSourceFromHBitmap(
                hBitmap,
                IntPtr.Zero,
                Int32Rect.Empty,
                BitmapSizeOptions.FromEmptyOptions());

            return wpfBitmap;
        }

        /// <summary>
        /// Ensures the icon files exist, creates them if not
        /// </summary>
        public static void EnsureIconsExist()
        {
            string resourcePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Resources");

            if (!Directory.Exists(resourcePath))
            {
                Directory.CreateDirectory(resourcePath);
            }

            string appIconPath = Path.Combine(resourcePath, "app.ico");
            string connectedIconPath = Path.Combine(resourcePath, "connected.ico");
            string disconnectedIconPath = Path.Combine(resourcePath, "disconnected.ico");

            if (!File.Exists(appIconPath))
            {
                SaveIcon(CreateAppIcon(256), appIconPath);
            }

            if (!File.Exists(connectedIconPath))
            {
                SaveIcon(CreateConnectedIcon(256), connectedIconPath);
            }

            if (!File.Exists(disconnectedIconPath))
            {
                SaveIcon(CreateDisconnectedIcon(256), disconnectedIconPath);
            }
        }

        /// <summary>
        /// Saves an icon to a file
        /// </summary>
        private static void SaveIcon(Icon icon, string path)
        {
            using var stream = new FileStream(path, FileMode.Create);
            icon.Save(stream);
        }
    }
}
