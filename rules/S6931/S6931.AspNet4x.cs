using System.Web.Mvc;

// Parameterized test: one test per action, wrapped in its own controller
[Route("[controller]")]
public class BasicsController : Controller
{
    [HttpGet]
    [Route("/Index2")]          // Noncompliant
    public ActionResult WithRouteAttribute() => View();

    [HttpGet]
    [Route("\\Index2")]         // Compliant
    public ActionResult WithBackslashAndRouteAttribute() => View();

    [HttpGet]
    [Route("Index1/SubPath")] // Compliant: not a root route
    public ActionResult WithSlashForSubPathAndHttpGetAttribute() => View();

    [HttpGet]
    [Route("Index2/SubPath")]   // Compliant: not a root route
    public ActionResult WithSlashForSubPathAndRouteAttribute() => View();

    [HttpGet]
    [Route("/IndexA")]          // Noncompliant
    [Route("/IndexB")]          // Noncompliant
    public ActionResult WithMultipleRouteAttributes() => View();
}

// Parameterized test: one test per action, wrapped in its own controller
public class WithAttributeSyntaxVariationsController : Controller
{
    [Route(template: @"/[action]", Name = "a", Order = 42)] // Noncompliant
    public ActionResult WithRouteAttributeNamedParameter() => View();

    [RouteAttribute(@"/[action]")]                          // Noncompliant
    public ActionResult WithAttributeSuffix() => View();

    [System.Web.Mvc.RouteAttribute(@"/[action]")] // Noncompliant
    public ActionResult WithFullQualifiedName() => View();

    [method:Route(@"/[action]")]                            // Noncompliant
    public ActionResult WithAttributeLocation() => View();
}

namespace WithAliases
{
    using MyRoute = RouteAttribute;
    using ASP = System.Web;

    public class WithAliasedRouteAttributeController : Controller // Noncompliant
    {
        [MyRoute(@"/[controller]")]
        public ActionResult Index() => View();
    }

    public class WithFullQualifiedPartiallyAliasedNameController : Controller // Noncompliant
    {
        [ASP.Mvc.RouteAttribute("A\\[action]")]
        public ActionResult Index() => View();
    }    
}

// Parameterized test: one test per action, wrapped in its own controller
public class WithAllTypesOfStringsController : Controller
{
    private const string AConst = "A";
    private const string ASlash = "/";

    [Route(@"/[action]")]          // Noncompliant
    public ActionResult WithVerbatimString() => View();

    [Route("/[action]")]           // Noncompliant
    public ActionResult WithEscapedString() => View();

    [Route("\u002f[action]")]      // Noncompliant: 2f is the Unicode code for '/'
    public ActionResult WithEscapeCode() => View();

    [Route($"/{AConst}/[action]")] // Noncompliant
    public ActionResult WithInterpolatedString() => View();

    [Route("""/[action]""")]       // Noncompliant
    public ActionResult WithRawStringLiteralsTriple() => View();

    [Route(""""/[action]"""")]     // Noncompliant
    public ActionResult WithRawStringLiteralsQuadruple() => View();

    [Route($$"""/{{AConst}}/[action]""")]                   // Noncompliant
    public ActionResult WithInterpolatedRawStringLiterals() => View();

    [Route(@"/[action]", Name = "a", Order = 42)]           // Noncompliant
    public ActionResult WithOptionalAttributeParameters() => View();

    [Route($"{AConst}/[action]")] // Compliant: resolves to a relative route
    public ActionResult WithInterpolatedStringResolvingToRelativeRoute() => View();

    [Route($"{ASlash}[action]")]  // Noncompliant: resolves to a root route
    public ActionResult WithInterpolatedStringResolvingToRootRoute() => View();
}
