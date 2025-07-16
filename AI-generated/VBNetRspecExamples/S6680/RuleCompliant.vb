Imports System.Linq
Imports Microsoft.AspNetCore.Mvc

Public Class S6680RuleCompliant
    Inherits Controller

    Public Shared MaxBoundary As Integer = 1337
    Public Shared MinBoundary As Integer = 1

    Public Function Compute(Data As Integer) As IActionResult
        If MinBoundary > Data Then
            Data = MinBoundary
        ElseIf Data > MaxBoundary Then
            Data = MaxBoundary
        End If

        For I As Integer = 0 To Data - 1
            Console.WriteLine("Hello")
        Next

        Enumerable.Range(1, Data).
            ToList().
            ForEach(Sub(I) Console.WriteLine("World"))

        Return Ok()
    End Function
End Class
