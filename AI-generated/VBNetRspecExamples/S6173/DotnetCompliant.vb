Imports Microsoft.AspNetCore.Mvc
Imports System.Linq

Public Class S6173DotnetCompliant
    Inherits Controller

    Private Shared ReadOnly EffectAllowList() As String = {
        "SepiaEffect",
        "BlackAndWhiteEffect",
        "WaterColorEffect",
        "OilPaintingEffect"
    }

    Public Function Apply(EffectName As String) As IActionResult
        If Not EffectAllowList.Contains(EffectName) Then
            Return BadRequest("Invalid effect name. The effect is not allowed.")
        End If

        Dim EffectInstance = Activator.CreateInstance(Nothing, EffectName)
        Dim EffectPlugin As Object = EffectInstance.Unwrap()

        If CType(EffectPlugin, IEffectCompliant).ApplyFilter() Then
            Return Ok()
        Else
            Return StatusCode(500, "Problem occurred")
        End If
    End Function
End Class

Public Interface IEffectCompliant
    Function ApplyFilter() As Boolean
End Interface
