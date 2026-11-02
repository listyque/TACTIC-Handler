using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Security.Cryptography;
using System.Windows.Forms;

internal static class Installer
{
    private static readonly string[] StateFolders = { "TACTIC-Handler/settings", "TACTIC-Handler/log", "TACTIC-Handler/custom_scripts", "D;" };

    private static string Under(string root, string relative)
    {
        string path = Path.GetFullPath(Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
        if (!path.StartsWith(Path.GetFullPath(root).TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("An archive path escapes the installation folder.");
        return path;
    }

    private static void NoLinks(string path)
    {
        for (var info = new DirectoryInfo(path); info != null; info = info.Parent)
            if (info.Exists && (info.Attributes & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Choose a folder without directory links: " + path);
    }

    private static string Hash(Stream stream)
    {
        using (var algorithm = SHA256.Create())
            return BitConverter.ToString(algorithm.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }

    private static void VerifyFiles(string root)
    {
        foreach (string line in File.ReadAllLines(Path.Combine(root, "SHA256SUMS")))
        {
            int separator = line.IndexOf("  ", StringComparison.Ordinal);
            if (separator != 64) throw new InvalidDataException("Invalid file inventory.");
            string name = line.Substring(separator + 2);
            bool mutable = false;
            foreach (string state in StateFolders)
                if (name == state || name.StartsWith(state + "/", StringComparison.Ordinal)) mutable = true;
            if (mutable) continue;
            string path = Under(root, name);
            using (var file = File.OpenRead(path))
                if (Hash(file) != line.Substring(0, separator))
                    throw new IOException("Preserve local application changes before installing: " + path);
        }
    }

    private static void CopyTree(string source, string target)
    {
        NoLinks(source);
        Directory.CreateDirectory(target);
        foreach (string path in Directory.GetFiles(source))
        {
            if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Setup will not replace linked state files: " + path);
            File.Copy(path, Path.Combine(target, Path.GetFileName(path)), true);
        }
        foreach (string path in Directory.GetDirectories(source))
            CopyTree(path, Path.Combine(target, Path.GetFileName(path)));
    }

    private static void CheckClosed(string target)
    {
        foreach (var process in Process.GetProcesses())
        {
            using (process)
            {
                try
                {
                    string path = process.MainModule.FileName;
                    if (path.StartsWith(target + "\\", StringComparison.OrdinalIgnoreCase))
                        throw new IOException("Close TACTIC Handler and its tray icon before updating this folder.");
                }
                catch (Win32Exception) { }
                catch (InvalidOperationException) { }
            }
        }
    }

    // Called by the UI and by the packaging check on a disposable target.
    internal static string Extract(string destination)
    {
        string target = Path.GetFullPath(destination).TrimEnd('\\', '/');
        if (target == Path.GetPathRoot(target).TrimEnd('\\', '/') || File.Exists(target))
            throw new IOException("Choose an application folder.");
        NoLinks(target);
        if (Directory.Exists(target) && Directory.GetFileSystemEntries(target).Length > 0
            && (!File.Exists(Path.Combine(target, "BUILD.json")) || !File.Exists(Path.Combine(target, "SHA256SUMS"))))
            throw new IOException("The selected folder is not a TACTIC Handler installation. Choose an empty folder.");
        CheckClosed(target);
        string stage = target + ".staging-" + Guid.NewGuid().ToString("N");
        Directory.CreateDirectory(stage);
        try
        {
        using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("handler.zip"))
        {
            if (Hash(stream) != PayloadHash.Value) throw new InvalidDataException("The setup payload is damaged.");
            stream.Position = 0;
            using (var archive = new ZipArchive(stream, ZipArchiveMode.Read))
                foreach (var entry in archive.Entries)
                {
                    if (!entry.FullName.StartsWith("TH/", StringComparison.Ordinal)
                        || ((entry.ExternalAttributes >> 16) & 0xf000) == 0xa000)
                        throw new InvalidDataException("Invalid setup archive entry.");
                    string name = entry.FullName.Substring(3);
                    if (name.Length == 0) continue;
                    string path = Under(stage, name);
                    if (entry.FullName.EndsWith("/")) { Directory.CreateDirectory(path); continue; }
                    Directory.CreateDirectory(Path.GetDirectoryName(path));
                    using (var source = entry.Open())
                    using (var output = File.Create(path)) source.CopyTo(output);
                }
        }
        VerifyFiles(stage);
        if (!File.Exists(Path.Combine(stage, "TH Setup.exe"))) throw new InvalidDataException("Setup launcher is missing.");
        string rollback = null;
        if (Directory.Exists(target))
        {
            CheckClosed(target);
            if (File.Exists(Path.Combine(target, "SHA256SUMS"))) VerifyFiles(target);
            foreach (string state in StateFolders)
            {
                string source = Under(target, state);
                if (Directory.Exists(source)) CopyTree(source, Under(stage, state));
            }
            CheckClosed(target);
            rollback = target + ".previous-" + DateTime.UtcNow.ToString("yyyyMMddTHHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 6);
            Directory.Move(target, rollback);
        }
        try { Directory.Move(stage, target); }
        catch { if (rollback != null) Directory.Move(rollback, target); throw; }
        return target;
        }
        finally
        {
            if (Directory.Exists(stage))
            {
                NoLinks(stage);
                // Only the freshly created sibling staging folder may be removed.
                if (Path.GetDirectoryName(stage) != Path.GetDirectoryName(target)
                    || !stage.StartsWith(target + ".staging-", StringComparison.Ordinal))
                    throw new IOException("Invalid staging cleanup path.");
                Directory.Delete(stage, true);
            }
        }
    }

    [STAThread]
    private static int Main()
    {
        Application.EnableVisualStyles();
        using (var picker = new FolderBrowserDialog())
        {
            picker.Description = "TACTIC Handler — choose an installation folder. Existing settings are preserved.";
            picker.SelectedPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "TACTIC Handler");
            if (picker.ShowDialog() != DialogResult.OK) return 0;
            using (var window = new Form())
            {
                window.Text = "TACTIC Handler Setup";
                window.Width = 520; window.Height = 140;
                window.StartPosition = FormStartPosition.CenterScreen;
                window.Controls.Add(new Label { Text = "Installing TACTIC Handler…", Dock = DockStyle.Top, Height = 40, Padding = new Padding(12) });
                window.Controls.Add(new ProgressBar { Style = ProgressBarStyle.Marquee, Dock = DockStyle.Bottom, Height = 24 });
                var worker = new BackgroundWorker();
                bool working = true;
                int exit = 0;
                window.FormClosing += delegate(object sender, FormClosingEventArgs args) { args.Cancel = working; };
                worker.DoWork += delegate(object sender, DoWorkEventArgs args) { args.Result = Extract(picker.SelectedPath); };
                worker.RunWorkerCompleted += delegate(object sender, RunWorkerCompletedEventArgs args)
                {
                    working = false;
                    if (args.Error != null)
                    {
                        MessageBox.Show(args.Error.Message, window.Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
                        exit = 1;
                    }
                    else
                    {
                        string root = (string)args.Result;
                        Process.Start(new ProcessStartInfo(Path.Combine(root, "TH Setup.exe")) { WorkingDirectory = root });
                    }
                    window.Close();
                };
                window.Shown += delegate { worker.RunWorkerAsync(); };
                Application.Run(window);
                return exit;
            }
        }
    }
}
