using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Routing;

[Route("[controller]")]
public class BasicsController : Controller
{
    [HttpGet("/Index1")]        // Noncompliant
    public IActionResult WithHttpGetAttribute() => View();

    [Route("/Index2")]          // Noncompliant
    public IActionResult WithRouteAttribute() => View();

    [HttpGet("\\Index1")]       // Compliant: backslash is not the root route
    public IActionResult WithBackslashAndHttpGetAttribute() => View();

    [Route("\\Index2")]         // Compliant
    public IActionResult WithBackslashAndRouteAttribute() => View();

    [HttpGet("Index1/SubPath")] // Compliant: not a root route
    public IActionResult WithSlashForSubPathAndHttpGetAttribute() => View();

    [Route("Index2/SubPath")]   // Compliant: not a root route
    public IActionResult WithSlashForSubPathAndRouteAttribute() => View();

    [Route("/IndexA")]          // Noncompliant
    [Route("/IndexB")]          // Noncompliant
    public IActionResult WithMultipleRouteAttributes() => View();

    [Route("/IndexC")]          // Noncompliant
    [HttpGet("/IndexD")]        // Noncompliant
    public IActionResult WithMixedRouteAndHttpGetAttributes() => View();
}

public class WithAllHttpMethodAttributesController : Controller
{
    [HttpGet("/IndexGet")]         // Noncompliant
    public IActionResult WithHttpGetAttribute() => View();

    [HttpPost("/IndexPost")]       // Noncompliant
    public IActionResult WithHttpPostAttribute() => View();

    [HttpPut("/IndexPut")]         // Noncompliant
    public IActionResult WithHttpPutAttribute() => View();

    [HttpDelete("/IndexDelete")]   // Noncompliant
    public IActionResult WithHttpDeleteAttribute() => View();

    [HttpPatch("/IndexPatch")]     // Noncompliant
    public IActionResult WithHttpPatchAttribute() => View();

    [HttpHead("/IndexHead")]       // Noncompliant
    public IActionResult WithHttpHeadAttribute() => View();

    [HttpOptions("/IndexOptions")] // Noncompliant
    public IActionResult WithHttpOptionsAttribute() => View();
}

public class WithUserDefinedAttributeDerivedFromHttpMethodAttributeController : Controller
{
    [MyHttpMethod("/Index")]       // Noncompliant: MyHttpMethodAttribute derives from HttpMethodAttribute
    public IActionResult WithUserDefinedAttribute() => View();

    private sealed class MyHttpMethodAttribute(string template) : HttpMethodAttribute([template]) { }
}

public class WithAttributeSyntaxVariationsController : Controller
{
    [Route(template: @"/[action]", Name = "a", Order = 42)] // Noncompliant
    public IActionResult WithRouteAttributeNamedParameter() => View();

    [RouteAttribute(@"/[action]")]                          // Noncompliant
    public IActionResult WithAttributeSuffix() => View();

    [Microsoft.AspNetCore.Mvc.RouteAttribute(@"/[action]")] // Noncompliant
    public IActionResult WithFullQualifiedName() => View();

    [method:Route(@"/[action]")]                            // Noncompliant
    public IActionResult WithAttributeLocation() => View();
}

namespace WithAliases
{
    using MyRoute = RouteAttribute;
    using ASP = Microsoft.AspNetCore;

    public class TestController : Controller
    {
        [MyRoute(@"/[controller]")]             // Noncompliant
        public IActionResult WithAliasedRouteAttribute() => View();

        [ASP.Mvc.RouteAttribute("A\\[action]")] // Noncompliant
        public IActionResult WithFullQualifiedPartiallyAliasedName() => View();
    }
}

public class WithAllTypesOfStringsController : Controller
{
    private const string AConst = "A";
    private const string ASlash = "/";

    [Route(@"/[action]")]          // Noncompliant
    public IActionResult WithVerbatimString() => View();

    [Route("/[action]")]           // Noncompliant
    public IActionResult WithEscapedString() => View();

    [Route("\u002f[action]")]      // Noncompliant: 2f is the Unicode code for '/'
    public IActionResult WithEscapeCode() => View();

    [Route($"/{AConst}/[action]")] // Noncompliant
    public IActionResult WithInterpolatedString() => View();

    [Route("""/[action]""")]       // Noncompliant
    public IActionResult WithRawStringLiteralsTriple() => View();

    [Route(""""/[action]"""")]     // Noncompliant
    public IActionResult WithRawStringLiteralsQuadruple() => View();

    [Route($$"""/{{AConst}}/[action]""")]                   // Noncompliant
    public IActionResult WithInterpolatedRawStringLiterals() => View();

    [Route(@"/[action]", Name = "a", Order = 42)]           // Noncompliant
    public IActionResult WithOptionalAttributeParameters() => View();

    [Route($"{AConst}/[action]")] // Compliant: resolves to a relative route
    public IActionResult WithInterpolatedStringResolvingToRelativeRoute() => View();

    [Route($"{ASlash}[action]")]  // Noncompliant: resolves to a root route
    public IActionResult WithInterpolatedStringResolvingToRootRoute() => View();
}
