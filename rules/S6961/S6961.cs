using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;

class ChildAttribute : ApiControllerAttribute { }
class GrandChildAttribute : ChildAttribute { }

public class ParentController : Controller { }
public class ParentControllerBase : ControllerBase { }

public class ChildController : ParentController { }
public class ChildControllerBase : ParentControllerBase { }

namespace SimpleCases
{
    [ApiController]
    public class Baseline : Controller { }              // Noncompliant {{Inherit from ControllerBase instead of Controller.}}
    //                      ^^^^^^^^^^

    [ApiController]
    public class ChildOfBase : ControllerBase { }       // Compliant

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
    public class NotAController : Controller { }        // Compliant, [NonController] is excluded

    [ApiController]
    internal class Internal : Controller { }            // Compliant, only raises at public methods
}

namespace SpecialAttributeUsages
{
    [type: ApiController]
    public class WithType : Controller { }          // Noncompliant
    //                      ^^^^^^^^^^
    [ApiControllerAttribute]
    public class WithSuffix : Controller { }        // Noncompliant
    //                        ^^^^^^^^^^
    [ApiController()]
    public class WithParentheses : Controller { }   // Noncompliant
    //                             ^^^^^^^^^^
    [type: ApiControllerAttribute()]
    public class Everything : Controller { }        // Noncompliant
    //                        ^^^^^^^^^^
}

namespace Inheritance
{
    [ApiController]
    public class Child : ParentController { }            // Compliant, we only check direct inheritance from "Controller"

    [ApiController]
    public class GrandChild : ChildController { }        // Compliant

    [ApiController]
    public class NoInheritance { }                       // Compliant
}

namespace CustomAttribute
{
    [ChildAttribute]
    public class UsesChildAttribute : Controller { }                 // Noncompliant
    //                                ^^^^^^^^^^

    [GrandChildAttribute]
    public class UsesGrandChildAttribute : Controller { }            // Noncompliant
    //                                     ^^^^^^^^^^

    [ChildAttribute]
    public class UsesChildAttributeBase : ControllerBase { }         // Compliant

    [GrandChildAttribute]
    public class UsesGrandChildAttributeBase : ControllerBase { }    // Compliant
}

namespace Partial
{
    [ApiController]
    public partial class Partial { }
    public partial class Partial : Controller { }       // Noncompliant
    //                             ^^^^^^^^^^

    [ApiController]
    public partial class PartialBase { }
    public partial class PartialBase : ControllerBase { }   // Compliant

    [ApiController]
    public partial class PartialDoubleInheritance : Controller { } // Noncompliant
    //                                              ^^^^^^^^^^
    public partial class PartialDoubleInheritance : Controller { } // Noncompliant as well
    //                                              ^^^^^^^^^^
}

namespace Nested
{
    public class Outer
    {
        // TODO: If we manage to raise ONLY on non-nested classes, make this Compliant. (Delete this comment during implementation.)
        [ApiController]
        public class Inner : Controller { }   // Noncompliant FP, this cannot be reached by ASP.NET.
    }
}

namespace MemberUsages
{
    // TODO: Hey implementer, please extract this to a [DataTestMethod] test, with the right-part of the invocation as a parameter.
    [ApiController]
    public class Invocations : Controller         // Compliant
    {
        object model = null;

        public object Foo() => View();
        public object Foo() => View("viewName");
        public object Foo() => View(model);
        public object Foo() => View("viewName", model);

        public object Foo() => PartialView();
        public object Foo() => PartialView("viewName");
        public object Foo() => PartialView(model);
        public object Foo() => PartialView("viewName", model);

        public object Foo() => ViewComponent("foo");
        public object Foo() => ViewComponent("foo", model);
        public object Foo() => ViewComponent(typeof(object));
        public object Foo() => ViewComponent(typeof(object), model);

        public object Foo() => Json(model);
        public object Foo() => Json(model, model);

        public object Foo() => OnActionExecutionAsync(default(ActionExecutingContext), default(ActionExecutionDelegate));
    }

    // TODO: Hey implementer, please extract this to a [DataTestMethod] test, with the right-part of the invocation as a parameter.
    [ApiController]
    public class VoidInvocations: Controller           // Compliant
    {
        public void Foo() => OnActionExecuted(default(ActionExecutedContext));
        public void Foo() => OnActionExecuting(default(ActionExecutingContext));
    }

    // TODO: Hey implementer, please extract this to a [DataTestMethod] test, with the right-part of the invocation as a parameter.
    [ApiController]
    public class Properties: Controller                 // Compliant
    {
        public object Foo() => ViewData;
        public object Foo() => ViewBag;
        public object Foo() => TempData;

        public object Foo() => ViewData["foo"];
        public object Foo() => ViewBag["foo"];
        public object Foo() => TempData["foo"];
    }

    // TODO: Hey implementer, please extract these "InXXX" one-liners to a [DataTestMethod] test.
    [ApiController]
    public class InConstructor: Controller              // Compliant
    {
        object foo;
        public InConstructor() => foo = View();
    }

    [ApiController]
    public class InDestructor: Controller               // Compliant
    {
        object foo;
        ~InDestructor() => foo = View();
    }

    [ApiController]
    public class InPropertyGet: Controller              // Compliant
    {
        object foo => View();
    }

    [ApiController]
    public class InPropertySet: Controller              // Compliant
    {
        object foo { set => _ = View(); }
    }

    [ApiController]
    public class InIndexer: Controller                 // Compliant
    {
        object this[int index] => View();
    }

    [ApiController]
    public class OverrideViewInvocation : Controller    // Compliant
    {
        public object Foo() => this.View();  // overrides and uses View
        public override ViewResult View() => null;
    }

    [ApiController]
    public class FakeViewInvocation : Controller        // Noncompliant
    //                                ^^^^^^^^^^
    {
        public object Foo() => this.View();   // hides View, does not override it
        public ViewResult View() => null;
    }

    [ApiController]
    public class BaseViewInvocation : Controller        // Compliant
    {
        public object Foo() => base.View();   // uses Controller.View
        public ViewResult View() => null;
    }

    [ApiController]
    public partial class Partial { }
    public partial class Partial : Controller { }       // Compliant
    public partial class Partial
    {
        public object Foo() => View();
    }

    [ApiController]
    public class MemberReference : Controller           // Compliant
    {
        public Func<ViewResult> NotCalled() => this.View;   // nothing is invoked, but the dependency is used.
    }

    [ApiController]
    public class NameOf : Controller                    // Compliant
    {
        public object Foo() => nameof(View); // same as above
    }

    [ApiController]
    public class PassByName : Controller                // Compliant
    {
        public void Foo() => ExpectsAction(View);
        public void ExpectsAction(Func<ViewResult> func)
        {
            // here func could be invoked or not.
        }
    }

    [ApiController]
    public class PassByLambda : Controller              // Compliant
    {
        public void Foo() => ExpectsAction(() => View());
        public void ExpectsAction(Func<ViewResult> func)
        {
            // here func could be invoked or not.
        }
    }
}
