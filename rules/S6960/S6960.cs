using Microsoft.AspNetCore.Mvc;

// Remark: secondary messages are asserted extensively, to ensure that grouping is done correctly and deterministically.

namespace TestInstrumentation
{
    public interface IServiceWithAnAPI { void Use(); }

    [ApiController]
    public class ApiController : ControllerBase { } // To shorten test cases declaration

    // ToDo: either replace with the actual interfaces from the NuGet dependencies or keep these interfaces
    // and implement the analyzer to ignore namespace and assembly, and only consider the name.
    // While that may introduce some false positives, the likelihood of that happening is very low.
    namespace WellKnownInterfacesExcluded
    {
        public interface ILogger<T> : IServiceWithAnAPI { }     // From Microsoft.Extensions.Logging
        public interface IMediator : IServiceWithAnAPI { }      // From MediatR
        public interface IMapper : IServiceWithAnAPI { }        // From AutoMapper
        public interface IConfiguration : IServiceWithAnAPI { } // From Microsoft.Extensions.Configuration
        public interface IBus : IServiceWithAnAPI { }           // From MassTransit
        public interface IMessageBus : IServiceWithAnAPI { }    // From NServiceBus
    }

    namespace WellKnownInterfacesNotExcluded
    {
        public interface IOption<T> : IServiceWithAnAPI { } // From Microsoft.Extensions.Options
    }

    namespace ResponsibilitySpecificServices
    {
        public interface IS1 : IServiceWithAnAPI { }
        public interface IS2 : IServiceWithAnAPI { }
        public interface IS3 : IServiceWithAnAPI { }
        public interface IS4 : IServiceWithAnAPI { }
        public interface IS5 : IServiceWithAnAPI { }
        public interface IS6 : IServiceWithAnAPI { }
    }
}

namespace WithInjectionViaPrimaryConstructors
{
    using TestInstrumentation.ResponsibilitySpecificServices;
    using TestInstrumentation.WellKnownInterfacesExcluded;
    using TestInstrumentation.WellKnownInterfacesNotExcluded;
    using TestInstrumentation;

    namespace AssertIssueLocationsAndMessage
    {
        // Noncompliant@+1: {{This controller has multiple responsibilities and could be split into 2 smaller units.}}
        public class TwoResponsibilities(IS1 s1, IS2 s2) : ApiController
        //           ^^^^^^^^^^^^^^^^^^^
        {
            public IActionResult A1() { s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            //                   ^^
            public IActionResult A2() { s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            //                   ^^
        }

        public class WithGenerics<T>(IS1 s1, IS2 s2) : ApiController // Noncompliant
        //           ^^^^^^^^^^^^
        {
            public IActionResult NonGenericAction() { s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            //                   ^^^^^^^^^^^^^^^^
            public IActionResult GenericAction<U>() { s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            //                   ^^^^^^^^^^^^^
        }

        public class @event<T>(IS1 s1, IS2 s2) : ApiController // Noncompliant
        //           ^^^^^^
        {
            public IActionResult @public() { s1.Use(); return Ok(); }  // Secondary {{Belongs to responsibility #1.}}
            //                   ^^^^^^^
            public IActionResult @private() { s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            //                   ^^^^^^^^
        }

        public class ThreeResponsibilities(IS1 s1, IS2 s2, IS3 s3) : ApiController // Noncompliant
        //           ^^^^^^^^^^^^^^^^^^^^^
        {
            public IActionResult A1() { s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { s3.Use(); return Ok(); } // Secondary {{Belongs to responsibility #3.}}
        }
    }

    namespace WithIOptions
    {
        // Compliant@+1: 4 deps injected, all well-known
        public class WellKnownDepsController(
            ILogger<WellKnownDepsController> logger, IMediator mediator, IMapper mapper, IConfiguration configuration) : ApiController
        {
            public IActionResult A1() { logger.Use(); return Ok(); }
            public IActionResult A2() { mediator.Use(); return Ok(); }
            public IActionResult A3() { mapper.Use(); return Ok(); }
            public IActionResult A4() { configuration.Use(); return Ok(); }
        }

        // Noncompliant@+1: 4 different Option<T> injected, that are not excluded
        public class FourDifferentOptionDepsController(
            IOption<int> o1, IOption<string> o2, IOption<bool> o3, IOption<double> o4) : ApiController
        {
            public IActionResult A1() { o1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { o2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { o3.Use(); return Ok(); } // Secondary {{Belongs to responsibility #3.}}
            public IActionResult A4() { o4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #4.}}
        }

        // Compliant@+1: 5 different Option<T> injected, used in couples to form a single responsibility
        public class FourDifferentOptionDepsUsedInCouplesController(
                   IOption<int> o1, IOption<string> o2, IOption<bool> o3, IOption<double> o4, IOption<int> o5) : ApiController
        {
            public IActionResult A1() { o1.Use(); o2.Use(); return Ok(); }
            public IActionResult A2() { o2.Use(); o3.Use(); return Ok(); }
            public IActionResult A3() { o3.Use(); o4.Use(); return Ok(); }
            public IActionResult A4() { o4.Use(); o5.Use(); return Ok(); }
        }

        // Noncompliant@+1: 3 Option<T> deps injected, the rest are well-known dependencies (used as well as unused)
        public class ThreeOptionDepsController(
            ILogger<WellKnownDepsController> logger, IMediator mediator, IMapper mapper, IConfiguration configuration,
            IOption<int> o1, IOption<string> o2, IOption<bool> o3) : ApiController
        {
            public IActionResult A1() { o1.Use(); logger.Use(); return Ok(); }        // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { o2.Use(); mediator.Use(); return Ok(); }      // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { o3.Use(); configuration.Use(); return Ok(); } // Secondary {{Belongs to responsibility #3.}}
            public IActionResult A4() { logger.Use(); return Ok(); }                  // Secondary {{Belongs to responsibility #4.}}
        }
    }

    namespace TwoActions
    {
        // Noncompliant@+1: 2 specific deps injected, each used in a separate responsibility, plus well-known dependencies
        public class TwoSeparateResponsibilitiesPlusSharedWellKnown(
            ILogger<TwoSeparateResponsibilitiesPlusSharedWellKnown> logger, IMediator mediator, IMapper mapper, IConfiguration configuration, IBus bus, IMessageBus messageBus,
            IS1 s1, IS2 s2) : ApiController
        {
            public IActionResult A1() { logger.Use(); mediator.Use(); bus.Use(); configuration.Use(); s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); bus.Use(); configuration.Use(); s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
        }

        // Noncompliant@+1: 4 specific deps injected, two for A1 and two for A2
        public class FourSpecificDepsTwoForA1AndTwoForA2(
            ILogger<FourSpecificDepsTwoForA1AndTwoForA2> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            public IActionResult A1() { logger.Use(); s1.Use(); s2.Use(); return Ok(); }                 // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
        }

        // Compliant@+1: 4 specific deps injected, two for A1 and two for A2, in non-API controller derived from Controller
        public class FourSpecificDepsTwoForA1AndTwoForA2NonApiFromController(
            ILogger<FourSpecificDepsTwoForA1AndTwoForA2NonApiController> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : Controller
        {
            public void A1() { logger.Use(); s1.Use(); s2.Use(); }
            public void A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); }
        }

        // Compliant@+1: 4 specific deps injected, two for A1 and two for A2, in non-API controller derived from ControllerBase
        public class FourSpecificDepsTwoForA1AndTwoForA2NonApiFromControllerBase(
            ILogger<FourSpecificDepsTwoForA1AndTwoForA2NonApiControllerBase> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ControllerBase
        {
            public void A1() { logger.Use(); s1.Use(); s2.Use(); }
            public void A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); }
        }

        // Compliant@+1: 4 specific deps injected, two for A1 and two for A2, in an API controller marked as NonController
        [NonController] public class FourSpecificDepsTwoForA1AndTwoForA2NoController(
            ILogger<FourSpecificDepsTwoForA1AndTwoForA2NoController> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            public IActionResult A1() { logger.Use(); s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); return Ok(); }
        }

        // Noncompliant@+1: 4 specific deps injected, two for A1 and two for A2, in a PoCo controller with controller suffix
        public class FourSpecificDepsTwoForA1AndTwoForA2PoCoController(
            ILogger<FourSpecificDepsTwoForA1AndTwoForA2PoCoController> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4)
        {
            public string A1() { logger.Use(); s1.Use(); s2.Use(); return "Ok"; }                 // Secondary {{Belongs to responsibility #1.}}
            public string A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); return "Ok"; } // Secondary {{Belongs to responsibility #2.}}
        }

        // Compliant@+1: 4 specific deps injected, two for A1 and two for A2, in a PoCo controller without controller suffix
        public class PoCoControllerWithoutControllerSuffix(
            ILogger<PoCoControllerWithoutControllerSuffix> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4)
        {
            public string A1() { logger.Use(); s1.Use(); s2.Use(); return "Ok"; }
            public string A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); return "Ok"; }
        }

        // Noncompliant@+1: 4 specific deps injected, two for A1 and two for A2, in a PoCo controller without controller suffix but with [Controller] attribute
        [Controller] public class PoCoControllerWithoutControllerSuffixWithControllerAttribute(
            ILogger<PoCoControllerWithoutControllerSuffixWithControllerAttribute> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4)
        {
            public string A1() { logger.Use(); s1.Use(); s2.Use(); return "Ok"; }                 // Secondary {{Belongs to responsibility #1.}}
            public string A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); return "Ok"; } // Secondary {{Belongs to responsibility #2.}}
        }

        // Noncompliant@+1: 4 specific deps injected, two for A1 and two for A2, with responsibilities in a different order
        public class FourSpecificDepsTwoForA1AndTwoForA2DifferentOrderOfResponsibilities(
            ILogger<FourSpecificDepsTwoForA1AndTwoForA2DifferentOrderOfResponsibilities> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            public IActionResult A2() { logger.Use(); s1.Use(); s2.Use(); return Ok(); }                 // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A1() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
        }

        // Noncompliant@+1: 4 specific deps injected, two for A1 and two for A2, with dependencies used in a different order
        public class FourSpecificDepsTwoForA1AndTwoForA2DifferentOrderOfDependencies(
            ILogger<FourSpecificDepsTwoForA1AndTwoForA2DifferentOrderOfDependencies> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            public IActionResult A1() { logger.Use(); s2.Use(); s1.Use(); return Ok(); }                 // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); s3.Use(); s4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
        }

        // Noncompliant@+1: 4 specific deps injected, three for A1 and one for A2
        public class FourSpecificDepsThreeForA1AndOneForA2(
            ILogger<FourSpecificDepsThreeForA1AndOneForA2> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS3 s4) : ApiController
        {
            public IActionResult A1() { logger.Use(); s1.Use(); s2.Use(); s3.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); s4.Use(); return Ok(); }     // Secondary {{Belongs to responsibility #2.}}
        }

        // Noncompliant@+1: 4 specific deps injected, all for A1 and none for A2
        public class FourSpecificDepsFourForA1AndNoneForA2(
            ILogger<FourSpecificDepsFourForA1AndNoneForA2> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS3 s4) : ApiController
        {
            public IActionResult A1() { logger.Use(); mediator.Use(); s1.Use(); s2.Use(); s3.Use(); s4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); return Ok(); }                                         // Secondary {{Belongs to responsibility #2.}}
        }

        // Compliant@+1: 4 specific deps injected, one in common between responsibility 1 and 2
        public class ThreeSpecificDepsOneInCommonBetweenA1AndA2(
            ILogger<ThreeSpecificDepsOneInCommonBetweenA1AndA2> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3) : ApiController
        {
            public IActionResult A1() { logger.Use(); mediator.Use(); s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { mediator.Use(); mapper.Use(); s2.Use(); s3.Use(); return Ok(); }
        }
    }

    namespace ThreeActions
    {
        // Noncompliant@+1: 2 specific deps injected, each used in a separate responsibility
        public class ThreeResponsibilities(
            ILogger<ThreeResponsibilities> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2) : ApiController
        {
            public IActionResult A1() { logger.Use(); mediator.Use(); s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { mapper.Use(); return Ok(); }                           // Secondary {{Belongs to responsibility #3.}}
        }

        // Noncompliant@+1: 3 specific deps injected, each used in a separate responsibility, possibly multiple times
        public class UpToThreeSpecificDepsController(
            ILogger<UpToThreeSpecificDepsController> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3) : ApiController
        {
            public IActionResult A1() { logger.Use(); s1.Use(); s1.Use(); return Ok(); }                           // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { logger.Use(); mapper.Use(); s2.Use(); s2.Use(); return Ok(); }             // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { mediator.Use(); mapper.Use(); s3.Use(); s3.Use(); s3.Use(); return Ok(); } // Secondary {{Belongs to responsibility #3.}}
        }

        // Noncompliant@+1: 3 specific deps injected, each used in a separate responsibility
        public class ThreeResponsibilities2(
            ILogger<ThreeResponsibilities2> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3) : ApiController
        {
            public IActionResult A1() { logger.Use(); mediator.Use(); s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { s3.Use(); return Ok(); }                               // Secondary {{Belongs to responsibility #3.}}
        }

        // Noncompliant@+1: 4 specific deps injected, two for A1, one for A2, and one for A3
        public class FourSpecificDepsTwoForA1OneForA2AndOneForA3(
            ILogger<FourSpecificDepsTwoForA1OneForA2AndOneForA3> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            public IActionResult A1() { logger.Use(); mediator.Use(); s1.Use(); s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); s3.Use(); return Ok(); }           // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { s4.Use(); return Ok(); }                                         // Secondary {{Belongs to responsibility #3.}}
        }

        // Noncompliant@+1: 4 specific deps injected, one for A1, one for A2, one for A3, one unused
        public class FourSpecificDepsOneForA1OneForA2OneForA3OneUnused(
            ILogger<FourSpecificDepsOneForA1OneForA2OneForA3OneUnused> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            public IActionResult A1() { logger.Use(); mediator.Use(); s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { mediator.Use(); mapper.Use(); s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A3() { s3.Use(); return Ok(); }                               // Secondary {{Belongs to responsibility #3.}}
        }

        // Compliant@+1: 4 specific deps injected, forming a single 3-cycle
        public class FourSpecificDepsFormingACycle(
            ILogger<FourSpecificDepsFormingACycle> logger, IMediator mediator, IMapper mapper,
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            // Cycle: A1, A2, A3
            public IActionResult A1() { logger.Use(); mediator.Use(); s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { mediator.Use(); mapper.Use(); s2.Use(); s3.Use(); return Ok(); }
            public IActionResult A3() { s3.Use(); s4.Use(); s1.Use(); return Ok(); }
        }
    }

    namespace SixActions
    {
        // Noncompliant@+1: 6 specific deps injected, forming 2 disconnected 3-cycles
        public class FourSpecificDepsFormingTwoDisconnectedCycles(
            IS1 s1, IS2 s2, IS3 s3, IS4 s4, IS5 s5, IS6 s6) : ApiController
        {
            // Cycle 1: A1, A2, A3
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { s2.Use(); s3.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A3() { s3.Use(); s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            // Cycle 2: A4, A5, A6 (disconnected from cycle 1)
            public IActionResult A4() { s4.Use(); s5.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A5() { s5.Use(); s6.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A6() { s6.Use(); s4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
        }

        // Compliant@+1: 5 specific deps injected, forming 2 connected 3-cycles
        public class FourSpecificDepsFormingTwoConnectedCycles(
            IS1 s1, IS2 s2, IS3 s3, IS4 s4, IS5 s5) : ApiController
        {
            // Cycle 1: A1, A2, A3
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { s2.Use(); s3.Use(); return Ok(); }
            public IActionResult A3() { s3.Use(); s1.Use(); return Ok(); }
            // Cycle 2: A4, A5, A6 (connected to cycle 1 via s1)
            public IActionResult A4() { s1.Use(); s4.Use(); return Ok(); }
            public IActionResult A5() { s4.Use(); s5.Use(); return Ok(); }
            public IActionResult A6() { s5.Use(); s1.Use(); return Ok(); }
        }

        // Compliant@+1: 4 specific deps injected, forming 2 3-cycles, connected by two dependencies (s1 and s2)
        public class FourSpecificDepsFormingTwoConnectedCycles2(
            IS1 s1, IS2 s2, IS3 s3, IS4 s4) : ApiController
        {
            // Cycle 1: A1, A2, A3
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { s2.Use(); s3.Use(); return Ok(); }
            public IActionResult A3() { s3.Use(); s1.Use(); return Ok(); }
            // Cycle 2: A4, A5, A6
            public IActionResult A4() { s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A5() { s2.Use(); s4.Use(); return Ok(); }
            public IActionResult A6() { s4.Use(); s1.Use(); return Ok(); }
        }

        // Compliant@+1: 4 specific deps injected, forming 2 3-cycles, connected by action invocations
        public class FourSpecificDepsFormingTwoConnectedCycles3(
            IS1 s1, IS2 s2, IS3 s3, IS4 s4, IS5 s5, IS6 s6) : ApiController
        {
            // Cycle 1: A1, A2, A3
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { s2.Use(); s3.Use(); return Ok(); }
            public IActionResult A3() { s3.Use(); s1.Use(); return Ok(); }
            // Cycle 2: A4, A5, A6, connected to cycle 1 via A1 invocation
            public IActionResult A4() { A1(); s4.Use(); return Ok(); }
            public IActionResult A5() { s5.Use(); s6.Use(); return Ok(); }
            public IActionResult A6() { s6.Use(); s4.Use(); return Ok(); }
        }

        // Noncompliant@+1: 6 specific deps injected, forming 3 disconnected 2-cycles
        public class FourSpecificDepsFormingThreeDisconnectedCycles(
            IS1 s1, IS2 s2, IS3 s3, IS4 s4, IS5 s5, IS6 s6) : ApiController
        {
            // Cycle 1: A1, A2
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { s2.Use(); s1.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            // Cycle 2: A3, A4
            public IActionResult A3() { s3.Use(); s4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A4() { s4.Use(); s3.Use(); return Ok(); } // Secondary {{Belongs to responsibility #2.}}
            // Cycle 3: A5, A6
            public IActionResult A5() { s5.Use(); s6.Use(); return Ok(); } // Secondary {{Belongs to responsibility #3.}}
            public IActionResult A6() { s6.Use(); s5.Use(); return Ok(); } // Secondary {{Belongs to responsibility #3.}}
        }

        // Noncompliant@+1: 6 specific deps injected, forming 2 connected 2-cycles and 1 disconnected 2-cycle
        public class FourSpecificDepsFormingTwoConnectedCyclesAndOneDisconnectedCycle(
            IS1 s1, IS2 s2, IS3 s3, IS4 s4, IS5 s5, IS6 s6) : ApiController
        {
            // Cycle 1: A1, A2
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); }       // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A2() { s2.Use(); s1.Use(); return Ok(); }       // Secondary {{Belongs to responsibility #1.}}
            // Cycle 2: A3, A4, connected to cycle 1 via A1 invocation
            public IActionResult A3() { A1(); s3.Use(); s4.Use(); return Ok(); } // Secondary {{Belongs to responsibility #1.}}
            public IActionResult A4() { s4.Use(); s3.Use(); return Ok(); }       // Secondary {{Belongs to responsibility #1.}}
            // Cycle 3: A5, A6
            public IActionResult A5() { s5.Use(); s6.Use(); return Ok(); }       // Secondary {{Belongs to responsibility #2.}}
            public IActionResult A6() { s6.Use(); s5.Use(); return Ok(); }       // Secondary {{Belongs to responsibility #2.}}
        }

        // Compliant@+1: 6 specific deps injected, forming 3 connected 2-cycles
        public class FourSpecificDepsFormingThreeConnectedCycles(
            IS1 s1, IS2 s2, IS3 s3, IS4 s4, IS5 s5, IS6 s6) : ApiController
        {
            // Cycle 1: A1, A2
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { s2.Use(); s1.Use(); return Ok(); }
            // Cycle 2: A3, A4, connected to cycle 1 via A1 invocation
            public IActionResult A3() { A1(); s3.Use(); s4.Use(); return Ok(); }
            public IActionResult A4() { s4.Use(); s3.Use(); return Ok(); }
            // Cycle 3: A5, A6, connected to cycle 1 via A2 invocation
            public IActionResult A5() { A2(); s5.Use(); s6.Use(); return Ok(); }
            public IActionResult A6() { s6.Use(); s5.Use(); return Ok(); }
        }

        // Compliant@+1: 6 specific deps injected, forming 3 connected 2-cycles - transitivity of connection
        public class FourSpecificDepsFormingThreeConnectedCyclesTransitivity(
                       IS1 s1, IS2 s2, IS3 s3, IS4 s4, IS5 s5, IS6 s6) : ApiController
        {
            // Cycle 1: A1, A2
            public IActionResult A1() { s1.Use(); s2.Use(); return Ok(); }
            public IActionResult A2() { s2.Use(); s1.Use(); return Ok(); }
            // Cycle 2: A3, A4, connected to cycle 1 via A1 invocation
            public IActionResult A3() { A1(); s3.Use(); s4.Use(); return Ok(); }
            public IActionResult A4() { s4.Use(); s3.Use(); return Ok(); }
            // Cycle 3: A5, A6, connected to cycle 1 via A2 invocation
            public IActionResult A5() { A3(); s5.Use(); s6.Use(); return Ok(); }
            public IActionResult A6() { s6.Use(); s5.Use(); return Ok(); }
        }
    }
}

// ToDo: to be continued
// - Member references are enough to establish the dependency, not necessarily invocations
// - Methods can depend on each other
// - Leniency for 1-2 deps, shared among all actions
// - namespace WithInjectionViaNonPrimaryConstructor { }
// - namespace WithInjectionViaServiceLocator { }
// - namespace WithInjectionViaSingletons { }
// - namespace WithUseInComplexBlocks { } // If statements, switch statements, switch expressions, loops, try-catch, scopes, local functions, nested local functions etc.

