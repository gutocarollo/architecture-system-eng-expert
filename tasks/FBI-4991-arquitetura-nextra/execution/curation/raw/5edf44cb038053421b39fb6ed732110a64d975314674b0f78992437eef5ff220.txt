using DomainCentric.ArchRules;
using DomainCentric.ArchRules.ContextMap;

namespace DcaShop.ArchitectureTests;

/// <summary>
/// Renders <c>docs/architecture/context-map.md</c> from the <c>[BoundedContext]</c>, <c>[Upstream]</c>,
/// <c>[ExternalUpstream]</c> and <c>[Partnership]</c> attributes — the context map as a fully derived view.
/// <para>
/// The test regenerates the file on every run and fails if it was stale, so CI catches a context map that
/// drifted from the declarations. The fix is always: commit the regenerated file. The strategic reading —
/// relationship patterns and subdomain types, which no attribute carries — is hand-maintained in
/// <c>project/domain.md</c> and is not touched here.
/// </para>
/// </summary>
public sealed class ContextMapDocumentationTest
{
    private static readonly string[] ContextMapPath = ["docs", "architecture", "context-map.md"];

    [Fact]
    public void ContextMapDocumentMatchesTheDeclaredContextMap()
    {
        var layout = DcaLayout.ForRootNamespace("DcaShop");
        var arch = DcaArchitecture.Load(
            layout,
            typeof(SharedKernel.SharedKernelContext).Assembly,
            typeof(Account.AccountContext).Assembly,
            typeof(Backoffice.BackofficeContext).Assembly,
            typeof(Portal.PortalContext).Assembly,
            typeof(Pricing.PricingContext).Assembly,
            typeof(Inventory.InventoryContext).Assembly,
            typeof(Product.ProductContext).Assembly,
            typeof(Cart.CartContext).Assembly,
            typeof(Checkout.CheckoutContext).Assembly);

        var generated = ContextMapRenderer.Of(arch).WithTitle("DcaShop Context Map").Render();
        Assert.Contains("Shopping Cart", generated, StringComparison.Ordinal);

        var root = FindRepositoryRoot();
        Assert.True(root is not null, "the repository root was not found, so the context map was never compared");

        var target = Path.Combine([root!, .. ContextMapPath]);
        var existing = File.Exists(target) ? File.ReadAllText(target) : null;

        Directory.CreateDirectory(Path.GetDirectoryName(target)!);
        File.WriteAllText(target, generated);

        Assert.True(
            generated == existing,
            "docs/architecture/context-map.md was stale and has been regenerated from the context attributes — review and commit it");
    }

    private static string? FindRepositoryRoot()
    {
        for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir is not null; dir = dir.Parent)
        {
            if (File.Exists(Path.Combine(dir.FullName, "DcaShop.sln")))
            {
                return dir.FullName;
            }
        }

        return null;
    }
}