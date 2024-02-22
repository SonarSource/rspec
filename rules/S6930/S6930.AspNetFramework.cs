using System.Web.Mvc;
using System;

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
    public ActionResult Index() => View();
}

public class BackslashOnActionUsingEscapeCharacter : Controller
{
    [Route("A\\[action]")]    // Noncompliant
    //       ^^
    public ActionResult Index() => View();
}

public class MultipleBackslashesOnAction : Controller
{
    [Route("A\\[action]\\B")] // Noncompliant
    //       ^^
    //                 ^^@-1
    public ActionResult Index() => View();
}

[Route("\\[controller]")]    // Noncompliant
//      ^^
public class RouteOnControllerStartingWithBackslash : Controller { }

public class AController : Controller
{
    //[Route("A\\[action]")]  // Compliant: commented out
    public ActionResult WithoutRouteAttribute() => View();

    [Route("A\\[action]", Name = "a", Order = 3)] // Noncompliant
    public ActionResult WithOptionalAttributeParameters() => View();

    [RouteAttribute("A\\[action]")] // Noncompliant
    public ActionResult WithAttributeSuffix() => View();

    [System.Web.Mvc.RouteAttribute("A\\[action]")] // Noncompliant
    public ActionResult WithFullQualifiedName() => View();

    [Route("A\\[action]")]  // Noncompliant
    [Route("B\\[action]")]  // Noncompliant
    [Route("C/[action]")]   // Compliant: forward slash is used
    public ActionResult WithMultipleRoutes() => View();

    [Route("A%5C[action]")] // Compliant: URL-escaped backslash is used
    public ActionResult WithUrlEscapedBackslash() => View();

    [Route("A/{s:regex(^(?!index\\b)[[a-zA-Z0-9-]]+$)}.html")]
    public ActionResult WithRegexContainingBackslashInLookahead(string s)  => View();  // Compliant: backslash is in regex

    [Route("A/{s:datetime:regex(\\d{{4}}-\\d{{2}}-\\d{{4}})}/B")]
    public ActionResult WithRegexContainingBackslashInMetaEscape(string s)  => View(); // Compliant: backslash is in regex
}

namespace WithAliases
{
    using MyRoute = RouteAttribute;
    using ASP = System.Web;

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

// ToDo: Remark for the implementer: suitable for a parameterized test
public class WithAllTypesOfStrings : Controller
{
    private const string ASlash = "/";
    private const string ABackSlash = @"\";
    private const string AConstStringIncludingABackslash = $"A{ABackSlash}";
    private const string AConstStringNotIncludingABackslash = $"A{ASlash}";

    [Route(AConstStringIncludingABackslash)]    // Noncompliant
    public ActionResult WithConstStringIncludingABackslash() => View();

    [Route(AConstStringNotIncludingABackslash)] // Compliant
    public ActionResult WithConstStringNotIncludingABackslash() => View();

    [Route("\u002f[action]")]                   // Compliant: 2f is the Unicode code for '/'
    public ActionResult WithEscapeCodeOfSlash() => View();

    [Route("\u005c[action]")]                   // Noncompliant: 5c is the Unicode code for '\'
    public ActionResult WithEscapeCodeOfBackslash() => View();

    [Route($"A{ASlash}[action]")]               // Compliant
    public ActionResult WithInterpolatedString() => View();

    [Route($@"A{ABackSlash}[action]")]          // Noncompliant
    public ActionResult WithInterpolatedVerbatimString() => View();

    [Route("""\[action]""")]                    // Noncompliant
    public ActionResult WithRawStringLiteralsTriple() => View();

    [Route(""""\[action]"""")]                  // Noncompliant
    public ActionResult WithRawStringLiteralsQuadruple() => View();

    [Route($$"""{{ABackSlash}}/[action]""")]    // Noncompliant
    public ActionResult WithInterpolatedRawStringLiteralsIncludingABackslash() => View();

    [Route($$"""{{ASlash}}/[action]""")]        // Complaint
    public ActionResult WithInterpolatedRawStringLiteralsNotIncludingABackslash() => View();
}
