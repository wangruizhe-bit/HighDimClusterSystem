# Prepare only the disposable GitHub Windows runner, never the user's desktop.
$ErrorActionPreference = "Stop"
if ($env:GITHUB_ACTIONS -ne "true") { throw "This script is only for GitHub Actions runners." }
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class CiDisplay {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct Mode {
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string device;
    public ushort specVersion, driverVersion, size, driverExtra;
    public uint fields;
    public int x, y;
    public uint orientation, fixedOutput;
    public short color, duplex, yResolution, ttOption, collate;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string formName;
    public ushort logPixels;
    public uint bitsPerPixel, width, height, flags, frequency;
    public uint icmMethod, icmIntent, mediaType, ditherType;
    public uint reserved1, reserved2, panningWidth, panningHeight;
  }
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  static extern bool EnumDisplaySettings(string device, int mode, ref Mode settings);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  static extern int ChangeDisplaySettings(ref Mode settings, uint flags);
  public static string Prepare() {
    Mode current = new Mode();
    current.size = (ushort)Marshal.SizeOf(typeof(Mode));
    if (!EnumDisplaySettings(null, -1, ref current)) throw new Exception("Cannot read desktop mode.");
    string before = current.width + "x" + current.height;
    if (current.width >= 1920 && current.height >= 1080) return before;
    current.width = 1920; current.height = 1080;
    current.fields |= 0x00080000 | 0x00100000;
    int test = ChangeDisplaySettings(ref current, 2);
    if (test != 0) throw new Exception("1920x1080 mode unsupported: " + test);
    int changed = ChangeDisplaySettings(ref current, 0);
    if (changed != 0) throw new Exception("Cannot set desktop mode: " + changed);
    if (!EnumDisplaySettings(null, -1, ref current) || current.width < 1920 || current.height < 1080)
      throw new Exception("Desktop resolution did not change.");
    return before + " -> " + current.width + "x" + current.height;
  }
}
'@
Write-Host ([CiDisplay]::Prepare())
