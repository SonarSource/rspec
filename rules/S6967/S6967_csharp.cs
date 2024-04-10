using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Mvc;

[assembly: ApiController] // This testcase should be on a dedicated test.
public class ControllerWithApiAttributeAtTheAssemblyLevel : ControllerBase
{
    [HttpPost("/[controller]")]
    public string Add(Movie movie)                                              // Compliant, ApiController attribute is applied at the assembly level.
    {
        return "Hello!";
    }
}

[ApiController]
public class ControllerWithApiAttributeAtTheClassLevel : ControllerBase
{
    [HttpPost("/[controller]")]
    public string Add(Movie movie)                                              // Compliant, ApiController attribute is applied at the class level.
    {
        return "Hello!";
    }
}

[Controller]
public class ControllerThatDoesNotInheritFromControllerBase
{
    [HttpPost("/[controller]")]
    public string Add(Movie movie)                                              // Compliant, ModelState is not available in this context.
    {
        return "Hello!";
    }
}

public class SimpleController
{
    [HttpPost("/[controller]")]
    public string Add(Movie movie)                                              // Compliant, ModelState is not available in this context.
    {
        return "Hello!";
    }
}

public class NonCompliantController : ControllerBase
{
    [HttpPost("/[controller]")]
    public string Post(Movie movie)                                             // Noncompliant
    {
        return "Hello!";
    }

    [HttpPut("/[controller]")]
    public string Put(Movie movie)                                              // Noncompliant
    {
        return "Hello!";
    }

    [HttpDelete("/[controller]")]
    public string Delete(Movie movie)                                           // Noncompliant
    {
        return "Hello!";
    }

    [HttpPatch("/[controller]")]
    public string Patch(Movie movie)                                            // Noncompliant
    {
        return "Hello!";
    }

    [HttpPost]
    [HttpPut]
    [HttpDelete]
    [HttpPatch]
    [Route("/[controller]/mix")]
    public string Mix([Required, FromQuery, EmailAddress] string email)         // Noncompliant
    {
        return "Hello!";
    }

    [AcceptVerbs("POST")]
    [Route("/[controller]/accept-verbs")]
    public string APost(Movie movie)                                            // Noncompliant
    {
        return "Hello!";
    }

    [AcceptVerbs("PUT")]
    [Route("/[controller]/accept-verbs")]
    public string APut(Movie movie)                                             // Noncompliant
    {
        return "Hello!";
    }

    [AcceptVerbs("DELETE")]
    [Route("/[controller]/accept-verbs")]
    public string ADelete(Movie movie)                                          // Noncompliant
    {
        return "Hello!";
    }

    [AcceptVerbs("PATCH")]
    [Route("/[controller]/accept-verbs")]
    public string APatch(Movie movie)                                           // Noncompliant
    {
        return "Hello!";
    }

    [AcceptVerbs("POST", "PUT", "DELETE", "PATCH")]
    [Route("/[controller]/many")]
    public string Many([Required, FromQuery, EmailAddress] string email)        // Noncompliant
    {
        return "Hello!";
    }

    [HttpPost("/[controller]/without-validation")]
    public string DtoWithoutValidation(DtoWithoutValidation dto)                // Compliant, DtoWithoutValidation does not have any validation attributes.
    {
        return "Hello!";
    }

    [HttpPost("/[controller]/custom-attribute-validation")]
    public string DtoWithCustomAttribute([ClassicMovie] string title)           // Noncompliant
    {
        return "Hello!";
    }

    [HttpPost("/[controller]/custom-validation")]
    public string DtoImplementingIValidatableObject(ValidatableMovie movie)     // Noncompliant
    {
        return "Hello!";
    }
}

public class Movie
{
    [Required]
    public string Title { get; set; }

    [Range(1900, 2200)]
    public int Year { get; set; }
}

public class DtoWithoutValidation
{
    public int? Id { get; set; }
    public string? Name { get; set; }
}

public class ClassicMovieAttribute : ValidationAttribute
{
    protected override ValidationResult? IsValid(object? value, ValidationContext validationContext)
    {
        return ValidationResult.Success;
    }
}

public class ValidatableMovie : IValidatableObject
{
    public int Id { get; set; }

    [Required]
    [StringLength(100)]
    public string Title { get; set; } = null!;

    public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
    {
        yield return new ValidationResult("Title is required", new[] { nameof(Title) });
    }
}
