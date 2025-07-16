Imports Microsoft.AspNetCore.Mvc

Public Class S6173DotnetNoncompliant
    Inherits Controller

    Public Function Apply(EffectName As String) As IActionResult
        Dim EffectInstance = Activator.CreateInstance(Nothing, EffectName) ' Noncompliant
        Dim EffectPlugin As Object = EffectInstance.Unwrap()

        If CType(EffectPlugin, IEffectNoncompliant).ApplyFilter() Then
            Return Ok()
        Else
            Return StatusCode(500, "Problem occurred")
        End If
    End Function
End Class

Public Interface IEffectNoncompliant
    Function ApplyFilter() As Boolean
End Interface
