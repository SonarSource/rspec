using Microsoft.AspNetCore.Mvc;

class MyApi : ApiControllerAttribute { }
class MyApiDerived : ApiControllerAttribute { }

public class BaseController : Controller { }
public class BaseControllerBase : ControllerBase { }

public class SecondBaseController : BaseController { }
public class SecondBaseControllerBase : BaseControllerBase { }

namespace SimpleCases
{
    [ApiController]
    public class Baseline : Controller { }               // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                      ^^^^^^^^^^

    [ApiController]
    public class DerivesBase : ControllerBase { }       // Compliant

    public class WithoutAttribute : Controller { }      // Compliant

    public class PocoController { }                     // Compliant

    [ApiController]
    public class PocoWithApiAttribute { }               // Compliant

    [Controller]
    public class PocoWithControllerAttribute { }        // Compliant

    [ApiController]
    [Controller]
    public class PocoWithBothAttributes { }             // Compliant, this is a very rare case, found <10 hits for [Controller] on SG

    [ApiController]
    [NonController]
    public class NotAController : Controller { }        // Compliant, see exception

    [ApiController]
    internal class Internal : Controller { }            // Compliant, see exception
}

namespace SpecialAttributeUsages
{
    [type: ApiController]
    public class WithType : Controller { }          // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                      ^^^^^^^^^^
    [ApiControllerAttribute]
    public class WithSuffix : Controller { }        // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                        ^^^^^^^^^^
    [ApiController()]
    public class WithParentheses : Controller { }   // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                             ^^^^^^^^^^
    [type: ApiControllerAttribute()]
    public class Everything : Controller { }        // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                        ^^^^^^^^^^
}

namespace Inheritance
{
    [ApiController]
    public class DerivesLevelOne : BaseController { }               // Compliant, we only check direct inheritance from "Controller"

    [ApiController]
    public class DerivesLevelTwo : SecondBaseController { }         // Compliant

    [ApiController]
    public class NoInheritance { }                                  // Compliant
}

namespace CustomAttribute
{
    [MyApi]
    public class UsesDerivedAttribute : Controller { }                  // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                                  ^^^^^^^^^^

    [MyApiDerived]
    public class UsesDerivedAttributeLevelTwo : Controller { }          // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                                          ^^^^^^^^^^

    [MyApi]
    public class UsesDerivedAttributeBase : ControllerBase { }         // Compliant

    [MyApiDerived]
    public class UsesDerivedAttributeBaseLevelTwo : ControllerBase { } // Compliant
}

namespace Partial
{
    public partial class Partial : Controller { }       // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                             ^^^^^^^^^^

    [ApiController]
    public partial class Partial { }

    public partial class PartialBase : Controller { }   // Compliant

    [ApiController]
    public partial class PartialBase { }                // Compliant
}

namespace Nested
{
    public class Outer
    {
        [ApiController]
        public class Inner : Controller { }   // Compliant, this cannot be reached. It can be an FP, since I think it's very rare.
        //                   ^^^^^^^^^^
    }
}

namespace Invocations
{
    [ApiController]
    public class UsesView : Controller                   // Compliant
    {
        public object Foo() => View();
    }

    [ApiController]
    public class UsesPartialView : Controller            // Compliant
    {
        public object Foo() => PartialView();
    }

    [ApiController]
    public class UsesViewComponent : Controller          // Compliant
    {
        public object Foo() => ViewComponent("foo");
    }

    [ApiController]
    public class FakeViewInvocation : Controller        // Noncompliant {{Inherit from ControllerBase instead of Controller}}
    //                                ^^^^^^^^^^
    {
        public object Foo() => this.View();   // hides View, does not override it
        public ViewResult View() => null;
    }

    [ApiController]
    public class OverrideViewInvocation : Controller    // Compliant
    {
        public object Foo() => this.View();  // overrides and uses View
        public override ViewResult View() => null;
    }

    public class NotInvoking : Controller               // Compliant
    {
        public object NameOf() => nameof(View);

        public void PassByName() => ExpectsAction(View); // Possible FP depending on what "ExpectsAction" does, just document it.

        public void PassByLambda() => ExpectsAction(() => View()); // Same as above

        public Func<ViewResult> NotCalled() => this.View; // Compliant, nothing is invoked

        public void ExpectsAction(Func<ViewResult> func) { }
    }

    [ApiController]
    public partial class Partial { }
    public partial class Partial : Controller { }     // Compliant
    public partial class Partial
    {
        public object Foo() => View();
    }
}
