"""
Integration tests for ALIS workflow graph.
"""
import pytest
from unittest.mock import MagicMock, patch
from backend.workflows.alis_graph import get_workflow, should_progress, should_remediate
from backend.models.state import ALISState


@pytest.fixture
def mock_nodes():
    """Mock all node functions."""
    with patch('backend.workflows.alis_graph.create_goal_path') as mock_create, \
         patch('backend.workflows.alis_graph.generate_material') as mock_material, \
         patch('backend.workflows.alis_graph.evaluate_test') as mock_eval:
        
        # Setup default return values
        mock_create.return_value = {
            'goal_id': 'test_goal',
            'path_structure': [{'id': 'c1', 'name': 'Concept 1', 'status': 'Open'}],
            'current_concept': None
        }
        
        mock_material.return_value = {
            'llm_output': 'Material generated',
            'current_concept': {'id': 'c1', 'name': 'Concept 1'}
        }
        
        mock_eval.return_value = {
            'test_evaluation_result': {'passed': True, 'score': 85},
            'current_concept': None  # No more concepts
        }
        
        yield {
            'create': mock_create,
            'material': mock_material,
            'eval': mock_eval
        }


class TestWorkflowRouting:
    def test_should_progress_next_concept(self):
        """Test routing to next concept when test passed and more concepts exist."""
        state = ALISState(
            user_id='test_user',
            test_passed=True,
            current_concept={'id': 'c2', 'name': 'Concept 2'}
        )
        
        result = should_progress(state)
        assert result == 'next_concept'
    
    def test_should_progress_goal_complete(self):
        """Test routing to goal complete when test passed and no more concepts."""
        state = ALISState(
            user_id='test_user',
            test_passed=True,
            current_concept=None
        )
        
        result = should_progress(state)
        assert result == 'goal_complete'
    
    def test_should_progress_re_study(self):
        """Test routing to re-study when test failed."""
        state = ALISState(
            user_id='test_user',
            test_passed=False,
            current_concept={'id': 'c1', 'name': 'Concept 1'}
        )
        
        result = should_progress(state)
        assert result == 're_study'
    
    def test_should_remediate_true(self):
        """Test remediation routing when needed."""
        state = ALISState(
            user_id='test_user',
            remediation_needed=True
        )
        
        result = should_remediate(state)
        assert result == 'remediate'
    
    def test_should_remediate_false(self):
        """Test remediation routing when not needed."""
        state = ALISState(
            user_id='test_user',
            remediation_needed=False
        )
        
        result = should_remediate(state)
        assert result == 'continue'


class TestWorkflowExecution:
    def test_workflow_creation(self):
        """Test that workflow can be created."""
        workflow = get_workflow()
        assert workflow is not None
        assert hasattr(workflow, 'stream')
    
    def test_workflow_has_required_nodes(self):
        """Test that workflow contains all required nodes."""
        workflow = get_workflow()
        
        # Get the graph structure
        graph = workflow.get_graph()
        nodes = list(graph.nodes.keys())
        
        # Verify key nodes exist
        assert 'P1_P3_Goal_Path_Creation' in nodes
        assert 'P4_Material_Generation' in nodes
        assert 'P6_Test_Evaluation' in nodes
    
    @patch('backend.workflows.alis_graph.create_goal_path')
    def test_workflow_execution_simple_path(self, mock_create):
        """Test a simple workflow execution path."""
        # Setup
        mock_create.return_value = {
            'goal_id': 'test_goal',
            'path_structure': [{'id': 'c1', 'name': 'Concept 1', 'status': 'Open'}],
            'current_concept': None,
            'user_profile': {'P2Enabled': False}
        }
        
        workflow = get_workflow()
        
        initial_state = ALISState(
            user_id='test_user',
            user_input='Learn Python',
            language='en',
            next_step='P1_P3_Goal_Path_Creation'
        )
        
        # Execute
        final_state = None
        for step in workflow.stream(initial_state, {"recursion_limit": 10}):
            final_state = step
        
        # Verify
        assert final_state is not None
        mock_create.assert_called_once()


class TestWorkflowStateTransitions:
    """Test state transitions through the workflow."""
    
    def test_state_preserves_user_id(self, mock_nodes):
        """Verify user_id is preserved through workflow."""
        workflow = get_workflow()
        
        initial_state = ALISState(
            user_id='user123',
            user_input='Test goal',
            next_step='P1_P3_Goal_Path_Creation'
        )
        
        final_state = None
        for step in workflow.stream(initial_state, {"recursion_limit": 5}):
            final_state = step
            # Check each intermediate state
            for node_name, node_state in step.items():
                assert node_state.get('user_id') == 'user123'
    
    def test_state_accumulates_data(self, mock_nodes):
        """Verify state accumulates data through nodes."""
        workflow = get_workflow()
        
        initial_state = ALISState(
            user_id='test_user',
            user_input='Learn ML',
            next_step='P1_P3_Goal_Path_Creation'
        )
        
        states = []
        for step in workflow.stream(initial_state, {"recursion_limit": 5}):
            states.append(step)
        
        # Verify data accumulation
        assert len(states) > 0
        final = states[-1]
        final_node_state = list(final.values())[0]
        
        # Should have goal_id from create_goal_path
        assert 'goal_id' in final_node_state
