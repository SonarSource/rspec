using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Routing;

// Parameterized test: one test per action
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

// Parameterized test: one test per action
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

public class WithUserDefinedAttributeDerivedFromHttpMethodAttributeController : Controller // Noncompliant: MyHttpMethodAttribute derives from HttpMethodAttribute
{
    [MyHttpMethod("/Index")]
    public IActionResult WithUserDefinedAttribute() => View();

    private sealed class MyHttpMethodAttribute(string template) : HttpMethodAttribute([template]) { }
}

// Parameterized test: one test per action, wrapped in its own controller
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

    public class WithAliasedRouteAttributeController : Controller // Noncompliant
    {
        [MyRoute(@"/[controller]")]             
        public IActionResult Index() => View();
    }

    public class WithFullQualifiedPartiallyAliasedNameController : Controller // Noncompliant
    {
        [ASP.Mvc.RouteAttribute("A\\[action]")]
        public IActionResult Index() => View();
    } 
}

// Parameterized test: one test per action, wrapped in its own controller
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

public class MultipleActionsAllRoutesStartingWithSlash1Controller : Controller  // Noncompliant
{
    [HttpGet("/Index1")]
    public IActionResult WithHttpGetAttribute() => View();

    [Route("/Index2")]
    public IActionResult WithRouteAttribute() => View();
}

public class MultipleActionsAllRoutesStartingWithSlash2Controller : Controller  // Noncompliant
{
    [HttpGet("/Index1")]
    [HttpGet("/Index3")]
    public IActionResult WithHttpGetAttribute() => View();

    [Route("/Index2")]
    [Route("/Index4")]
    [HttpGet("/Index5")]
    public IActionResult WithRouteAttribute() => View();
}

[Route("[controller]")]
public class MultipleActionsAllRoutesStartingWithSlash3Controller : Controller  // Noncompliant
{
    [HttpGet("/Index1")]
    [HttpGet("/Index3")]
    public IActionResult WithHttpGetAttribute() => View();

    [Route("/Index2")]
    [Route("/Index4")]
    [HttpGet("/Index5")]
    public IActionResult WithRouteAttribute() => View();
}

public class MultipleActionsSomeRoutesStartingWithSlash1Controller : Controller // Compliant: some routes are relative
{
    [HttpGet("Index1")]         
    public IActionResult WithHttpGetAttribute() => View();

    [Route("/Index2")]
    public IActionResult WithRouteAttribute() => View();
}

public class MultipleActionsSomeRoutesStartingWithSlash2Controller : Controller // Compliant: some routes are relative
{
    [HttpGet("Index1")]
    [HttpGet("/Index1")]
    public IActionResult WithHttpGetAttribute() => View();

    [Route("/Index2")]
    public IActionResult WithRouteAttribute() => View();
}

public class MultipleActionsSomeRoutesStartingWithSlash3Controller : Controller // Compliant: some routes are relative
{
    [HttpGet("Index1")]
    [HttpPost("/Index1")]
    public IActionResult WithHttpGetAttribute() => View();

    [Route("/Index2")]
    public IActionResult WithRouteAttribute() => View();
}
