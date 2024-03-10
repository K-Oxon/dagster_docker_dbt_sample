import os
from pathlib import Path

from dagster import Definitions, OpExecutionContext
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    build_schedule_from_dbt_selection,
    dbt_assets,
)

dbt_project_dir = Path(__file__).joinpath("..", "dbt_projects", "jaffle_shop").resolve()
dbt_profiles_dir = Path(__file__).joinpath("..", "dbt_projects").resolve()

dbt = DbtCliResource(
    project_dir=os.fspath(dbt_project_dir), profiles_dir=os.fspath(dbt_profiles_dir)
)

# If DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is set, a manifest will be created at runtime.
# Otherwise, we expect a manifest to be present in the project's target directory.
if os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"):
    dbt_parse_invocation = dbt.cli(["parse"], manifest={}).wait()
    dbt_manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")
else:
    dbt_manifest_path = dbt_project_dir.joinpath("target", "manifest.json")

# experimental
# see https://docs.dagster.io/integrations/dbt/reference#loading-dbt-tests-as-asset-checks
dagster_dbt_translator = DagsterDbtTranslator(
    settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)
)


@dbt_assets(
    manifest=dbt_manifest_path,
    dagster_dbt_translator=dagster_dbt_translator,
)
def jaffle_shop_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


daily_dbt_assets_schedule = build_schedule_from_dbt_selection(
    [jaffle_shop_dbt_assets],
    job_name="all_assets_daily_job",
    cron_schedule="0 0 * * *",
    dbt_select="fqn:*",
)

defs = Definitions(
    assets=[jaffle_shop_dbt_assets],
    schedules=[daily_dbt_assets_schedule],
    resources={
        "dbt": dbt,
    },
)
