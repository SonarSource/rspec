using System.Web.Mvc;

[Route("[controller]")]
public class NoncompliantController : Controller // Noncompliant {{Change the paths of the actions of this controller to be relative and adapt the controller route accordingly.}}
//           ^^^^^^^^^^^^^^^^^^^^^^
{
    [Route("/Index1")]                  // Secondary
    //     ^^^^^^^^^
    public ActionResult Index1() => View();

    [Route("/SubPath/Index2_1")]        // Secondary
    //     ^^^^^^^^^^^^^^^^^^^
    [Route("/[controller]/Index2_2")]   // Secondary
    //     ^^^^^^^^^^^^^^^^^^^^^^^^        
    public ActionResult Index2() => View();

    [Route("/[action]")]                // Secondary
    //     ^^^^^^^^^^^
    public ActionResult Index3() => View();

    [Route("/SubPath/Index4_1")]        // Secondary
    //     ^^^^^^^^^^^^^^^^^^^
    [Route("/[controller]/Index4_2")]   // Secondary
    //     ^^^^^^^^^^^^^^^^^^^^^^^^
    public ActionResult Index4() => View();
}

[RoutePrefix("[controller]")]
public class NoncompliantWithRoutePrefixController : Controller // Noncompliant {{Change the paths of the actions of this controller to be relative and adapt the controller route accordingly.}}
//           ^^^^^^^^^^^^^^^^^^^^^^
{
    [Route("/Index1")]                  // Secondary
    //     ^^^^^^^^^
    public ActionResult Index1() => View();
}

[Route("[controller]")]
[Route("[controller]/[action]")]
public class NoncompliantMultiRouteController : Controller // Noncompliant {{Change the paths of the actions of this controller to be relative and adapt the controller route accordingly.}}
//           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
{
    [Route("/Index1")]                  // Secondary
    //     ^^^^^^^^^
    public ActionResult Index1() => View();

    [Route("/SubPath/Index2_1")]        // Secondary
    //     ^^^^^^^^^^^^^^^^^^^
    [Route("/[controller]/Index2_2")]   // Secondary
    //     ^^^^^^^^^^^^^^^^^^^^^^^^    
    public ActionResult Index2() => View();

    [Route("/[action]")]                // Secondary
    //     ^^^^^^^^^^^
    public ActionResult Index3() => View();
}

[Route("[controller]")]
public class CompliantController : Controller // Compliant: at least one action has at least a relative route
{
    [Route("/Index1")]
    public ActionResult Index1() => View();

    [Route("/SubPath/Index2")]
    public ActionResult Index2() => View();

    [Route("/[action]")]
    public ActionResult Index3() => View();

    [Route("/[controller]/Index4_1")]
    [Route("SubPath/Index4_2")] // The relative route
    public ActionResult Index4() => View();
}

public class NoncompliantNoControllerRouteController : Controller // Noncompliant {{Change the paths of the actions of this controller to be relative and add a controller route with the common prefix.}}
{
    [Route("/Index1")]                          // Secondary
    public ActionResult Index1() => View();

    [Route("/SubPath/Index2_1")]                // Secondary
    [Route("/[controller]/Index2_2")]           // Secondary 
    public ActionResult Index2() => View();

    [Route("/[action]")]                        // Secondary
    public ActionResult Index3() => View();
}

public class CompliantNoControllerRouteNoActionRouteController : Controller // Compliant
{
    public ActionResult Index1() => View(); // Default route -> relative

    [Route("/SubPath/Index2")]
    public ActionResult Index2() => View();

    [Route("/[action]")]
    public ActionResult Index3() => View();

    [Route("/SubPath/Index4_1")]
    [Route("/[controller]/Index4_2")]
    public ActionResult Index4() => View();
}

public class CompliantNoControllerRouteEmptyActionRouteController : Controller // Compliant
{
    [Route]
    public ActionResult Index1() => View(); // Empty route -> relative

    [Route("/SubPath/Index2")]
    public ActionResult Index2() => View();

    [Route("/[action]")]
    public ActionResult Index3() => View();

    [Route("/SubPath/Index4_1")]
    [Route("/[controller]/Index4_2")]
    public ActionResult Index4() => View();
}

// Parameterized test: there should be one dedicated test per action, wrapped in its own controller.
// The noncompliant/compliant comment should be moved from the action level to the controller level.
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

// Parameterized test: there should be one dedicated test per action, wrapped in its own controller.
// The noncompliant/compliant comment should be moved from the action level to the controller level.
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
        [MyRoute(@"/[controller]")] // Secondary
        public ActionResult Index() => View();
    }

    public class WithFullQualifiedPartiallyAliasedNameController : Controller // Noncompliant
    {
        [ASP.Mvc.RouteAttribute("A\\[action]")] // Secondary
        public ActionResult Index() => View();
    }    
}

// Parameterized test: there should be one dedicated test per action, wrapped in its own controller.
// The noncompliant/compliant comment should be moved from the action level to the controller level.
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
