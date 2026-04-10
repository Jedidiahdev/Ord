from pathlib import Path


class ProductizationExporter:
    """Exports a lightweight Next.js + Supabase + Stripe starter package."""

    def export(self, target_dir: str, app_name: str) -> Path:
        root = Path(target_dir) / app_name
        root.mkdir(parents=True, exist_ok=True)

        (root / "README.md").write_text(
            "# One-Click Productized App\n"
            "Generated with Ord Productization Exporter.\n\n"
            "## Stack\n- Next.js\n- Supabase\n- Stripe\n"
        )
        (root / ".env.example").write_text(
            "NEXT_PUBLIC_SUPABASE_URL=\n"
            "NEXT_PUBLIC_SUPABASE_ANON_KEY=\n"
            "STRIPE_SECRET_KEY=\n"
        )
        (root / "package.json").write_text(
            '{"name":"productized-app","private":true,"scripts":{"dev":"next dev","build":"next build"}}'
        )

        return root
