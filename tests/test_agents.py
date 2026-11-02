"""Tests for agent functionality."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from backend.agents.base_agent import BaseAgent, IntegrationAgent


@pytest.mark.agent
class TestBaseAgent:
    """Tests for BaseAgent class."""

    @patch("backend.agents.base_agent.create_llm")
    def test_base_agent_initialization(self, mock_create_llm):
        """Test BaseAgent initialization."""
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        agent = BaseAgent(
            system_prompt="Test prompt",
            model_name="test-model",
            temperature=0.5,
        )

        assert agent.system_prompt == "Test prompt"
        assert agent.llm == mock_llm
        mock_create_llm.assert_called_once_with(
            model_name="test-model", temperature=0.5
        )

    @patch("backend.agents.base_agent.create_llm")
    @pytest.mark.asyncio
    async def test_base_agent_process(self, mock_create_llm):
        """Test BaseAgent message processing."""
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value="Agent response")
        mock_create_llm.return_value = mock_llm

        agent = BaseAgent()
        agent.chain = mock_chain

        response = await agent.process("Test message")

        assert response == "Agent response"
        mock_chain.ainvoke.assert_called_once()

    @patch("backend.agents.base_agent.create_llm")
    @pytest.mark.asyncio
    async def test_base_agent_process_with_context(self, mock_create_llm):
        """Test BaseAgent processing with context."""
        mock_llm = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="Agent response with context")
        mock_create_llm.return_value = mock_llm

        agent = BaseAgent()
        agent.chain = mock_chain

        context = {"user_id": "123", "channel": "slack"}
        response = await agent.process("Test message", context=context)

        assert response == "Agent response with context"
        # Verify context was included in the input
        call_args = mock_chain.ainvoke.call_args
        assert "Context:" in call_args[0][0]["input"]

    @patch("backend.agents.base_agent.create_llm")
    @pytest.mark.asyncio
    async def test_base_agent_process_error_handling(self, mock_create_llm):
        """Test BaseAgent error handling."""
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(side_effect=Exception("Test error"))
        mock_create_llm.return_value = mock_llm

        agent = BaseAgent()
        agent.chain = mock_chain

        response = await agent.process("Test message")

        assert "Error processing message" in response
        assert "Test error" in response


@pytest.mark.agent
class TestIntegrationAgent:
    """Tests for IntegrationAgent class."""

    @patch("backend.agents.base_agent.create_llm")
    def test_integration_agent_initialization(self, mock_create_llm):
        """Test IntegrationAgent initialization."""
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        agent = IntegrationAgent()

        assert agent.system_prompt is not None
        assert "multi-channel communication platform" in agent.system_prompt
        assert agent.llm == mock_llm

    @patch("backend.agents.base_agent.create_llm")
    @pytest.mark.asyncio
    async def test_integration_agent_process(self, mock_create_llm):
        """Test IntegrationAgent message processing."""
        mock_llm = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="Integration agent response")
        mock_create_llm.return_value = mock_llm

        agent = IntegrationAgent()
        agent.chain = mock_chain

        response = await agent.process("Hello")

        assert response == "Integration agent response"
        mock_chain.ainvoke.assert_called_once()
