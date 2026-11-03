using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

internal static class SetupPresets
{
    private const string Magic = "TH_SETUP_CFG_001";
    private const int MaxConfig = 65536;
    private static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = MaxConfig };
    private static readonly string[] Keys = { "server", "project", "install_folder", "repository_name", "plugins", "shelf", "shortcuts" };

    internal static Dictionary<string, object> Defaults(Dictionary<string, object> value)
    {
        return (Dictionary<string, object>)value["defaults"];
    }

    internal static string Text(Dictionary<string, object> defaults, string key, string fallback = "")
    {
        object value;
        return defaults.TryGetValue(key, out value) ? (string)value : fallback;
    }

    private static Dictionary<string, object> Parse(string data, bool ownVersion)
    {
        var value = Json.DeserializeObject(data) as Dictionary<string, object>;
        if (value == null || value.Count != 3 || !value.ContainsKey("format") || !value.ContainsKey("version") || !value.ContainsKey("defaults")
            || !(value["format"] is int) || (int)value["format"] != 1 || !(value["version"] is string)
            || !Regex.IsMatch((string)value["version"], @"^\d+\.\d+\.\d+\.\d+$")
            || (ownVersion && (string)value["version"] != PayloadHash.Version))
            throw new InvalidDataException("Invalid TH setup metadata.");
        var defaults = value["defaults"] as Dictionary<string, object>;
        if (defaults == null || defaults.Keys.Any(key => !Keys.Contains(key)))
            throw new InvalidDataException("Setup presets may contain only public deployment settings. Credentials are not allowed.");
        foreach (string key in new[] { "server", "project", "install_folder", "repository_name", "shelf" })
        {
            object item;
            if (defaults.TryGetValue(key, out item) && (!(item is string) || ((string)item).Length > 2048 || ((string)item).Any(char.IsControl)))
                throw new InvalidDataException("Invalid setup preset: " + key);
        }
        string server = Text(defaults, "server");
        Uri uri;
        if (server.Length > 0 && (!Uri.TryCreate(server, UriKind.Absolute, out uri) || (uri.Scheme != "http" && uri.Scheme != "https")
            || uri.UserInfo.Length > 0 || uri.Query.Length > 0 || uri.Fragment.Length > 0 || uri.AbsolutePath != "/"))
            throw new InvalidDataException("Enter a server root URL without embedded credentials.");
        string name = Text(defaults, "repository_name", "repo");
        if (new[] { "runtime", "tactic-handler", "build.json", "sha256sums", "setup-defaults.json", "setup-template.bin" }.Contains(name.ToLowerInvariant()))
            throw new InvalidDataException("Choose a repository folder name that does not belong to the application.");
        if (name.Length == 0 || name == "." || name == ".." || name.EndsWith(".") || name.Trim() != name
            || name.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 || Regex.IsMatch(name.Split('.')[0], @"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$", RegexOptions.IgnoreCase))
            throw new InvalidDataException("Invalid repository folder name.");
        object plugins;
        if (defaults.TryGetValue("plugins", out plugins) && plugins != null)
        {
            var items = plugins as object[];
            if (items == null || items.Length > 64 || items.Any(item => !(item is string) || !Regex.IsMatch((string)item, @"^[A-Za-z]\w*$")))
                throw new InvalidDataException("Invalid DCC plugin presets.");
        }
        object shortcuts;
        if (defaults.TryGetValue("shortcuts", out shortcuts) && !(shortcuts is bool))
            throw new InvalidDataException("Invalid shortcut preset.");
        return value;
    }

    internal static Dictionary<string, object> ReadInstaller()
    {
        using (var stream = File.OpenRead(Assembly.GetExecutingAssembly().Location))
        using (var reader = new BinaryReader(stream))
        {
            if (stream.Length < Magic.Length + 8) throw new InvalidDataException("Setup metadata is missing.");
            stream.Position = stream.Length - Magic.Length - 8;
            ulong length = reader.ReadUInt64();
            if (Encoding.ASCII.GetString(reader.ReadBytes(Magic.Length)) != Magic || length == 0 || length > MaxConfig
                || length > (ulong)(stream.Length - Magic.Length - 8))
                throw new InvalidDataException("Setup metadata is damaged.");
            stream.Position = stream.Length - Magic.Length - 8 - (long)length;
            return Parse(Encoding.UTF8.GetString(reader.ReadBytes((int)length)), true);
        }
    }

    internal static string PreviousRepository(string root)
    {
        string path = Path.Combine(root, "setup-defaults.json");
        if (!File.Exists(path)) return "repo";
        if (new FileInfo(path).Length > MaxConfig) throw new InvalidDataException("Setup metadata is too large.");
        return Text(Defaults(Parse(File.ReadAllText(path, Encoding.UTF8), false)), "repository_name", "repo");
    }

    internal static void Install(string stage, Dictionary<string, object> value)
    {
        File.WriteAllText(Path.Combine(stage, "setup-defaults.json"), Json.Serialize(value), new UTF8Encoding(false));
        string template = Path.Combine(stage, "setup-template.bin");
        File.Copy(Assembly.GetExecutingAssembly().Location, template, true);
        using (var source = File.OpenRead(template))
            File.WriteAllText(template + ".sha256", Installer.Hash(source) + "  setup-template.bin\n");
    }
}
