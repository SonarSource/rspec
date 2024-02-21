using Microsoft.AspNetCore.Mvc;
using System.Diagnostics.CodeAnalysis;

[Route(@"A\[controller]")]    // Noncompliant {{Replace this `\` with `/`.}}
//        ^
public class BackslashOnControllerUsingVerbatimString : Controller { }

[Route("A\\[controller]")]    // Noncompliant
//       ^^
public class BackslashOnControllerUsingEscapeCharacter : Controller { }

[Route("A\\[controller]\\B")] // Noncompliant
//       ^^
//                     ^^@-1
public class MultipleBackslashesOnController : Controller { }

public class BackslashOnActionUsingVerbatimString : Controller
{
    [Route(@"A\[action]")]    // Noncompliant
    //        ^
    public IActionResult Index() => View();
}

public class BackslashOnActionUsingEscapeCharacter : Controller
{
    [Route("A\\[action]")]    // Noncompliant
    //       ^^
    public IActionResult Index() => View();
}

public class MultipleBackslashesOnAction : Controller
{
    [Route("A\\[action]\\B")] // Noncompliant
    //       ^^
    //                 ^^@-1
    public IActionResult Index() => View();
}

[Route("\\[controller]")]    // Noncompliant
//      ^^
public class RouteOnControllerStartingWithBackslash : Controller { }

public class AController : Controller
{
    //[Route("A\\[action]")]  // Compliant: commented out
    public IActionResult WithoutRouteAttribute() => View();

    [Route("A\\[action]", Name = "a", Order = 3)] // Noncompliant
    public IActionResult WithOptionalAttributeParameters() => View();

    [Route("A/[action]", Name = @"a\b", Order = 3)] // Compliant: backslash is on the name
    public IActionResult WithBackslashInRouteName() => View();

    [RouteAttribute("A\\[action]")] // Noncompliant
    public IActionResult WithAttributeSuffix() => View();

    [Microsoft.AspNetCore.Mvc.RouteAttribute("A\\[action]")] // Noncompliant
    public IActionResult WithFullQualifiedName() => View();

    [Route("A\\[action]")]  // Noncompliant
    [Route("B\\[action]")]  // Noncompliant
    [Route("C/[action]")]   // Compliant: forward slash is used
    public IActionResult WithMultipleRoutes() => View();

    [Route("A%5C[action]")] // Compliant: URL-escaped backslash is used
    public IActionResult WithUrlEscapedBackslash() => View();

    [Route("A/{s:regex(^(?!index\\b)[[a-zA-Z0-9-]]+$)}.html")]
    public IActionResult WithRegexContainingBackslashInLookahead(string s)  => View();  // Compliant: backslash is in regex

    [Route("A/{s:datetime:regex(\\d{{4}}-\\d{{2}}-\\d{{4}})}/B")]
    public IActionResult WithRegexContainingBackslashInMetaEscape(string s)  => View(); // Compliant: backslash is in regex
}

namespace WithAliases
{
    using MyRoute = RouteAttribute;
    using ASP = Microsoft.AspNetCore;

    [MyRoute(@"A\[controller]")]            // Noncompliant
    public class WithAliasedRouteAttribute : Controller { }

    [ASP.Mvc.RouteAttribute("A\\[action]")] // Noncompliant
    public class WithFullQualifiedPartiallyAliasedName : Controller { }
}

namespace WithFakeRouteAttribute
{
    [Route(@"A\[controller]")]      // Compliant: not a real RouteAttribute
    public class AController : Controller { }

    [AttributeUsage(AttributeTargets.Class)]
    public class RouteAttribute : Attribute
    {
        public RouteAttribute(string template) { }
    }
}

public class WithAllTypesOfStrings : Controller
{
    private const string ASlash = "/";
    private const string ABackslash = @"\";
    private const string AConstStringIncludingABackslash = $"A{ABackslash}";
    private const string AConstStringNotIncludingABackslash = $"A{ASlash}";

    [Route(AConstStringIncludingABackslash)]    // Noncompliant
    public IActionResult WithConstStringIncludingABackslash() => View();

    [Route(AConstStringNotIncludingABackslash)] // Compliant
    public IActionResult WithConstStringNotIncludingABackslash() => View();

    [Route("\u002f[action]")]                   // Compliant: 2f is the Unicode code for '/'
    public IActionResult WithEscapeCodeOfSlash() => View();

    [Route("\u005c[action]")]                   // Noncompliant: 5c is the Unicode code for '\'
    public IActionResult WithEscapeCodeOfBackslash() => View();

    [Route($"A{ASlash}[action]")]               // Compliant
    public IActionResult WithInterpolatedString() => View();

    [Route($@"A{ABackslash}[action]")]          // Noncompliant
    public IActionResult WithInterpolatedVerbatimString() => View();

    [Route("""\[action]""")]                    // Noncompliant
    public IActionResult WithRawStringLiteralsTriple() => View();

    [Route(""""\[action]"""")]                  // Noncompliant
    public IActionResult WithRawStringLiteralsQuadruple() => View();

    [Route($$"""{{ABackslash}}/[action]""")]    // Noncompliant
    public IActionResult WithInterpolatedRawStringLiteralsIncludingABackslash() => View();

    [Route($$"""{{ASlash}}/[action]""")]        // Complaint
    public IActionResult WithInterpolatedRawStringLiteralsNotIncludingABackslash() => View();
}

public class WithHttpMethodAttributeAndAllTypesOfStrings : Controller
{
    private const string ASlash = "/";
    private const string ABackslash = @"\";
    private const string AConstStringIncludingABackslash = $"A{ABackslash}";
    private const string AConstStringNotIncludingABackslash = $"A{ASlash}";

    [HttpGet(AConstStringIncludingABackslash)]     // Noncompliant
    public IActionResult WithConstStringIncludingABackslash() => View();

    [HttpPost(AConstStringNotIncludingABackslash)] // Compliant
    public IActionResult WithConstStringNotIncludingABackslash() => View();

    [HttpPatch("\u002f[action]")]                  // Compliant: 2f is the Unicode code for '/'
    public IActionResult WithEscapeCodeOfSlash() => View();

    [HttpHead("\u005c[action]")]                   // Noncompliant: 5c is the Unicode code for '\'
    public IActionResult WithEscapeCodeOfBackslash() => View();

    [HttpDelete($"A{ASlash}[action]")]             // Compliant
    public IActionResult WithInterpolatedString() => View();

    [HttpOptions($@"A{ABackslash}[action]")]       // Noncompliant
    public IActionResult WithInterpolatedVerbatimString() => View();

    [HttpGet("""\[action]""")]                     // Noncompliant
    public IActionResult WithRawStringLiteralsTriple() => View();

    [HttpPost(""""\[action]"""")]                  // Noncompliant
    public IActionResult WithRawStringLiteralsQuadruple() => View();

    [HttpPatch($$"""{{ABackslash}}/[action]""")]   // Noncompliant
    public IActionResult WithInterpolatedRawStringLiteralsIncludingABackslash() => View();

    [HttpHead($$"""{{ASlash}}/[action]""")]        // Complaint
    public IActionResult WithInterpolatedRawStringLiteralsNotIncludingABackslash() => View();
}

class WithMapControllerRoute
{
    private const string ASlash = "/";
    private const string ABackslash = @"\";

    void Test(WebApplication app)
    {
        const string ASlashLocal = "A";
        const string ABackslashLocal = @"B";

        app.MapControllerRoute("default", "{controller=Home}\\{action=Index}/{id?}");                  // Noncompliant
        app.MapControllerRoute("default", @"{controller=Home}\\{action=Index}/{id?}");                 // Noncompliant
        app.MapControllerRoute("default", "{controller=Home}/{action=Index}/{id?}");                   // Compliant

        app.MapControllerRoute("default", $$"""{controller=Home}{{ABackslash}}{action=Index}""");      // Noncompliant
        app.MapControllerRoute("default", $$"""{controller=Home}{{ASlash}}{action=Index}""");          // Compliant
        app.MapControllerRoute("default", $$"""{controller=Home}{{ABackslashLocal}}{action=Index}"""); // Noncompliant
        app.MapControllerRoute("default", $$"""{controller=Home}{{ASlashLocal}}{action=Index}""");     // Compliant

        app.MapControllerRoute(
            name: "default",
            pattern: "{controller=Home}\\{action=Index}/{id?}", // Noncompliant
            defaults: new { controller = "Home", action = "Index" });
        app.MapControllerRoute(
            pattern: "{controller=Home}\\{action=Index}/{id?}", // Noncompliant
            name: "default",
            defaults: new { controller = "Home", action = "Index" });
    }
}

class WithUserDefinedSyntaxRouteParameter
{
    const string RouteConst = "Route";

    void Test()
    {
        AMethodWithStringSyntaxRouteParameter("\\");      // Noncompliant
        AMethodWithStringSyntaxRouteConstParameter("\\"); // Noncompliant
        AMethodWithStringSyntaxNonRouteParameter("\\");   // Compliant
        AMethodWithNoStringSyntax("\\");                  // Compliant
    }

    private void AMethodWithStringSyntaxRouteParameter([StringSyntax("Route")]string route) { }
    private void AMethodWithStringSyntaxRouteConstParameter([StringSyntax(RouteConst)]string route) { }
    private void AMethodWithStringSyntaxNonRouteParameter([StringSyntax("NonRoute")]string route) { }
    private void AMethodWithNoStringSyntax(string route) { }
}
