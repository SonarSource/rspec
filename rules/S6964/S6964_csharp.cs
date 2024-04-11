using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;
using System.ComponentModel.DataAnnotations;

public class ClassNotUsedInRequests
{
    int ValueProperty { get; set; }                                             // Compliant
}

public class ModelUsedInControler
{
    public int ValueProperty { get; set; }                                      // Noncompliant
    public int? NullableValueProperty { get; set; }                             // Compliant
    [Required] public int RequiredValueProperty { get; set; }                   // Compliant
    [ValidateNever] public int NotValidatedValueProperty { get; set; }          // Compliant
    [Range(0, 10)] public int ValuePropertyWithRangeValidation { get; set; }    // Noncompliant
    [Required] public int? RequiredNullableValueProperty { get; set; }          // Compliant
    public int PropertyWithPrivateSetter { get; private set; }                  // Compliant
    protected int ProtectedProperty { get; set; }                               // Compliant
    internal int InternalProperty { get; set; }                                 // Compliant
    protected internal int ProtectedInternalProperty { get; set; }              // Compliant
    private int PrivateProperty { get; set; }                                   // Compliant
    public int ReadOnlyProperty => 42;                                          // Compliant
    public int field = 42;                                                      // Compliant

#nullable enable
    public string NonNullableReferenceProperty { get; set; }                    // Noncompliant
    [Required] public string RequiredNonNullableReferenceProperty { get; set; } // Compliant
    public string? NullableReferenceProperty { get; set; }                      // Compliant
#nullable disable
    public string ReferenceProperty { get; set; }                               // Compliant
}

public class DerivedFromController : Controller
{
    [HttpPost]
    public IActionResult Create(ModelUsedInControler model)
    {
        return View(model);
    }
}

[Controller]
public class DecoratedWithControllerAttribute // better suited for parameterized UTs
{
    [HttpGet] public IActionResult Get(ModelUsedInControler model) => null;
    [HttpPost] public IActionResult Post(ModelUsedInControler model) => null;
    [HttpPut] public IActionResult Put(ModelUsedInControler model) => null;
    [HttpDelete] public IActionResult Delete(ModelUsedInControler model) => null;
}

[ApiController]
[Route("api/[controller]")]
public class DecoratedWithApiControlerAttribute : ControllerBase
{
    [HttpGet]
    public int Single(ModelUsedInControler model) => 42;

    [HttpGet]
    [HttpPost]
    [HttpPut]
    [HttpDelete]
    public int Multiple(ModelUsedInControler model) => 42;

    [AcceptVerbs("POST")]
    public int Verb(ModelUsedInControler model) => 42;

    [AcceptVerbs("GET", "POST", "PUT", "DELETE")]
    public int MultipleVerbs(ModelUsedInControler model) => 42;
}