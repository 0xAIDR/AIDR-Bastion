import asyncio
from datetime import datetime

from app.core.enums import ActionStatus
from app.core.pipeline import BasePipeline
from app.db.crud import event_crud
from app.db.session import async_session
from app.models.pipeline import PipelineResult, TaskResult
from app.modules.kafka_client import KafkaClient
from app.utils import get_pipelines_from_config
from settings import get_settings


class BastionApp:
    """
    Manages the execution of multiple pipelines based on configuration.

    This class coordinates the task process by loading pipeline configurations
    and executing the appropriate pipelines for each pipeline flow. It determines the
    final pipeline status based on the results from all active pipelines.
    """

    def __init__(self):
        """
        Initialize the BastionApp with configuration from settings.

        Loads pipeline configuration from settings and creates a mapping of
        pipeline flows to their corresponding pipeline instances.
        """
        self.settings = get_settings()
        pipelines_config: list[dict] = self.settings.PIPELINE_CONFIG
        self.pipeline_flows: dict[str, list[BasePipeline]] = get_pipelines_from_config(pipelines_config)

        if self.settings.KAFKA:
            self.kafka_client = KafkaClient()
        else:
            self.kafka_client = None

    def __task_status(self, task_result: list[PipelineResult]) -> ActionStatus:
        """
        Determine the overall task status based on individual pipeline results.

        Args:
            task_result: List of PipelineResult objects from individual pipelines

        Returns:
            ActionStatus: The overall status based on the most severe result:
                - BLOCK if any pipeline returned BLOCK
                - NOTIFY if any pipeline returned NOTIFY (and no BLOCK)
                - ALLOW if all pipelines returned ALLOW or no results
        """
        if not task_result:
            return ActionStatus.ALLOW
        if any(result.status == ActionStatus.BLOCK for result in task_result):
            return ActionStatus.BLOCK
        if any(result.status == ActionStatus.NOTIFY for result in task_result):
            return ActionStatus.NOTIFY
        return ActionStatus.ALLOW

    def __send_to_kafka(self, prompt: str, task: TaskResult, task_id: str | int | None = None):
        if not self.kafka_client:
            return
        if task.status in (ActionStatus.BLOCK, ActionStatus.NOTIFY):
            payload = task.model_dump()
            payload.update(
                {
                    "service": self.settings.PROJECT_NAME,
                    "version": self.settings.VERSION,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            if self.settings.KAFKA.save_prompt:
                payload["prompt"] = prompt
            if task_id:
                payload["task_id"] = task_id
            self.kafka_client.send_message(payload)

    async def __save_to_db(
        self, prompt: str, task: TaskResult, pipeline_flow: str, task_id: str | int | None = None
    ) -> None:
        """
        Save event to database.

        Args:
            prompt: Analyzed prompt
            task: Task result
            pipeline_flow: Pipeline flow name
            task_id: Optional task identifier
        """
        try:
            async with async_session() as session:
                event_data = {
                    "task_id": str(task_id) if task_id else None,
                    "prompt": prompt if self.settings.DATABASE_SAVE_PROMPT else None,
                    "status": task.status.value,
                    "flow_name": pipeline_flow,
                    "pipeline_results": task.model_dump(mode="json"),
                }
                await event_crud.create(session, obj_in=event_data)
                await session.commit()
        except Exception as e:
            from app.modules.logger import bastion_logger

            bastion_logger.error(f"Failed to save event to database: {e}")

    async def run(self, prompt: str, pipeline_flow: str, task_id: str | int | None = None) -> TaskResult:
        """
        Executes the task process for a given prompt using the specified pipeline flow.

        Args:
            prompt: The text to be analyzed for malicious content
            pipeline_flow: The pipeline flow type (e.g., 'base', 'code') that determines
                     which pipelines to use

        Returns:
            TaskResult: Contains the overall task status and individual pipeline results.
                       Only includes pipelines that returned BLOCK or NOTIFY status.
        """
        pipelines = self.pipeline_flows.get(pipeline_flow, [])
        if not pipelines:
            return TaskResult(status=ActionStatus.ALLOW, pipelines=[])
        pipeline_results = await asyncio.gather(*[pipeline.run(prompt) for pipeline in pipelines])
        pipelines_result = [
            result for result in pipeline_results if result.status in (ActionStatus.BLOCK, ActionStatus.NOTIFY)
        ]
        status = self.__task_status(pipelines_result)
        task = TaskResult(status=status, pipelines=pipelines_result)

        # Send to Kafka if configured
        self.__send_to_kafka(prompt=prompt, task_id=task_id, task=task)

        # Save to database
        await self.__save_to_db(prompt=prompt, task=task, pipeline_flow=pipeline_flow, task_id=task_id)

        return task


bastion_app: BastionApp = BastionApp()
