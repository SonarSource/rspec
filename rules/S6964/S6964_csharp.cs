using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;
using System.ComponentModel.DataAnnotations;

public class ClassNotUsedInRequests
{
    int ValueProperty { get; set; }                                             // Compliant
}

public struct Struct { public int Foo { get; set; } }
public record struct RecordStruct {  public int Foo { get; set; }

public class ModelUsedInController
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

    public Struct StructValueProperty { get; set; }                             // Noncompliant
    public RecordStruct RecordStructValueProperty { get; set; }                 // Noncompliant

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
    public IActionResult Create(ModelUsedInController model)
    {
        return View(model);
    }
}

[Controller]
public class DecoratedWithControllerAttribute // better suited for parameterized UTs
{
    [HttpGet] public IActionResult Get(ModelUsedInController model) => null;
    [HttpPost] public IActionResult Post(ModelUsedInController model) => null;
    [HttpPut] public IActionResult Put(ModelUsedInController model) => null;
    [HttpDelete] public IActionResult Delete(ModelUsedInController model) => null;
}

[ApiController]
[Route("api/[controller]")]
public class DecoratedWithApiControlerAttribute : ControllerBase
{
    [HttpGet]
    public int Single(ModelUsedInController model) => 42;

    [HttpGet]
    [HttpPost]
    [HttpPut]
    [HttpDelete]
    public int Multiple(ModelUsedInController model) => 42;

    [AcceptVerbs("POST")]
    public int Verb(ModelUsedInController model) => 42;

    [AcceptVerbs("GET", "POST", "PUT", "DELETE")]
    public int MultipleVerbs(ModelUsedInController model) => 42;
}