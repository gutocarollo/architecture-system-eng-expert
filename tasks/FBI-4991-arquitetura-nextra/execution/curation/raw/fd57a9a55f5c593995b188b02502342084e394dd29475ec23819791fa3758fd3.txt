using DomainCentric.BuildingBlocks.Ddd.Strategic;

namespace DcaShop.Backoffice;

/// <summary>
/// Backoffice bounded context: operating this application. A <b>generic</b> subdomain — one would rather buy an
/// operator console than build it — and a bounded context nonetheless, because it owns a language: an <i>event
/// publication</i> is a dispatched domain event with a completion status, a term no business context uses.
/// </summary>
/// <remarks>
/// It reads what other contexts have already published and negotiates no contract with any of them, so it declares
/// no upstream relationships: Separate Ways on the context map. In transaction-script style it has no domain model
/// of its own, which the pattern-selection decision allows for a generic subdomain.
/// <para>
/// Context-specific admin pages (editing a product, a price, a stock level) belong in their own bounded context
/// under <c>/backoffice/{context}/</c>, not here. This context holds what belongs to no business context: today the
/// event-publication log, later dashboards and admin navigation.
/// </para>
/// </remarks>
[BoundedContext("Backoffice",
    Description = "Operating this application: event publication log, dashboards, operator views")]
public static class BackofficeContext
{
    /// <summary>Path prefix every backoffice page lives under, and the scope of its own authentication.</summary>
    public const string PathPrefix = "/backoffice";
}