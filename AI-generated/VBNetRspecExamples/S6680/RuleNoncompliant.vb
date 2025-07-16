Imports System.Linq
Imports Microsoft.AspNetCore.Mvc

Public Class S6680RuleNoncompliant
    Inherits Controller

    Public Function Compute(Data As Integer) As IActionResult
        For I As Integer = 0 To Data - 1 ' Noncompliant
            Console.WriteLine("Hello")
        Next

        Enumerable.Range(1, Data). ' Noncompliant
            ToList().
            ForEach(Sub(I) Console.WriteLine("World"))

        Return Ok()
    End Function
End Class
