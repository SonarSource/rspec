Imports Microsoft.AspNetCore.Mvc
Imports System.Text.RegularExpressions

Public Class S2631DotnetNoncompliant
    Inherits Controller

    Public Function Validate(RegexPattern As String, Input As String) As IActionResult
        Dim Match As Boolean = Regex.IsMatch(Input, RegexPattern)

        Return Json(Match)
    End Function
End Class
