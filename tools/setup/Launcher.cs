using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class Launcher
{
    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            string root = AppDomain.CurrentDomain.BaseDirectory;
            string application = Path.Combine(root, "TACTIC-Handler");
            string python = Path.Combine(root, "runtime", "pythonw.exe");
            string script = Path.Combine(application, "launch.py");
            if (!File.Exists(python) || !File.Exists(script))
                throw new FileNotFoundException("Keep the EXE together with the runtime and TACTIC-Handler folders.");
#if SETUP_BUILDER
            string arguments = "-I -B -X utf8 -m thlib.ui.setup_wizard --builder";
#elif SETUP_WIZARD
            string arguments = "-I -B -X utf8 -m thlib.ui.setup_wizard";
#else
            string arguments = "-I -B -X utf8 \"" + script + "\"";
#endif
#if SETUP_WIZARD || SETUP_BUILDER
            foreach (string argument in args)
                if (argument == "--smoke" || argument == "--ru")
                    arguments += " " + argument;
#endif
            var start = new ProcessStartInfo(python, arguments);
            start.WorkingDirectory = root;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            if (String.IsNullOrWhiteSpace(start.EnvironmentVariables["TACTIC_HANDLER_SETTINGS_DIR"]))
            {
                string profile = application;
                if (File.Exists(Path.Combine(root, "TACTIC Stream.exe")))
                {
                    string edition = File.Exists(Path.Combine(root, "demo", "manifest.json"))
                        ? "TACTIC Stream Demo" : "TACTIC Stream";
                    profile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), edition, "handler");
                }
                start.EnvironmentVariables["TACTIC_HANDLER_SETTINGS_DIR"] = profile;
            }
            using (Process child = Process.Start(start))
            {
                child.WaitForExit();
                if (child.ExitCode != 0)
                    MessageBox.Show("TACTIC Handler exited with code " + child.ExitCode
                        + ". Check the application log in "
                        + Path.Combine(start.EnvironmentVariables["TACTIC_HANDLER_SETTINGS_DIR"], "log") + ".",
                        "TACTIC Handler", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return child.ExitCode;
            }
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "TACTIC Handler", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
