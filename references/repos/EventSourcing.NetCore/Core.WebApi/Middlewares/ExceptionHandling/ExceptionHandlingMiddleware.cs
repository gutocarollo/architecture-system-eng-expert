using System.ComponentModel.DataAnnotations;
using System.Net;
using Core.Exceptions;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.DependencyInjection;

namespace Core.WebApi.Middlewares.ExceptionHandling;

public class ExceptionToProblemDetailsHandler(Func<Exception, HttpContext, ProblemDetails?>? customExceptionMap)
    : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken
    )
    {
        var details = customExceptionMap?.Invoke(exception, httpContext) ?? exception.MapToProblemDetails();

        httpContext.Response.StatusCode = details.Status ?? StatusCodes.Status500InternalServerError;
        await httpContext.Response
            .WriteAsJsonAsync(
                new ProblemDetails
                {
                    Title = "An error occurred",
                    Detail = exception.Message,
                    Type = exception.GetType().Name,
                    Status = (int)HttpStatusCode.BadRequest
                }, cancellationToken: cancellationToken).ConfigureAwait(false);

        return true;
    }
}

public static class ExceptionHandlingMiddleware
{
    public static IServiceCollection AddDefaultExceptionHandler(
        this IServiceCollection serviceCollection,
        Func<Exception, HttpContext, ProblemDetails?>? customExceptionMap = null
    ) =>
        serviceCollection
            .AddSingleton<IExceptionHandler>(new ExceptionToProblemDetailsHandler(customExceptionMap))
            .AddProblemDetails();
}

public static class ProblemDetailsExtensions
{
    public static ProblemDetails MapToProblemDetails(this Exception exception)
    {
        var statusCode = exception switch
        {
            ArgumentException _ => StatusCodes.Status400BadRequest,
            ValidationException _ => StatusCodes.Status400BadRequest,
            UnauthorizedAccessException _ => StatusCodes.Status401Unauthorized,
            InvalidOperationException _ => StatusCodes.Status403Forbidden,
            AggregateNotFoundException  => StatusCodes.Status404NotFound,
            NotImplementedException _ => StatusCodes.Status501NotImplemented,
            _ => StatusCodes.Status500InternalServerError
        };

        return exception.MapToProblemDetails(statusCode);
    }

    public static ProblemDetails MapToProblemDetails(
        this Exception exception,
        int statusCode,
        string? title = null,
        string? detail = null
    ) =>
        new() { Title = title ?? exception.GetType().Name, Detail = detail ?? exception.Message, Status = statusCode };
}
