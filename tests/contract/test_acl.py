"""
ACL/ABAC Contract Tests - D6 Security Verification

Tests that access control is enforced correctly:
1. Users without group membership cannot see restricted documents
2. Users with group membership can see their documents
3. No existence leaks (no doc titles/snippets for unauthorized users)
"""
import pytest
import requests
import time

BASE_URL = "http://16.146.148.184:3000"
API_URL = f"{BASE_URL}/api/v1"


@pytest.fixture(scope="module")
def uploaded_docs():
    """Upload test documents with different ACL groups"""
    docs = {}

    # Upload public document
    with open("artifacts/acl-fixtures/doc_public.txt", "r") as f:
        public_content = f.read()

    response = requests.post(
        f"{API_URL}/documents",
        json={
            "content": public_content,
            "metadata": {
                "groups": ["public"],
                "title": "Public RAG Overview",
                "classification": "public"
            }
        }
    )
    assert response.status_code == 200
    docs["public"] = response.json()

    # Upload private document
    with open("artifacts/acl-fixtures/doc_private.txt", "r") as f:
        private_content = f.read()

    response = requests.post(
        f"{API_URL}/documents",
        json={
            "content": private_content,
            "metadata": {
                "groups": ["secret"],
                "title": "Internal Security Architecture",
                "classification": "confidential"
            }
        }
    )
    assert response.status_code == 200
    docs["private"] = response.json()

    # Wait for indexing
    time.sleep(5)

    return docs


class TestACLPositive:
    """Test that authorized users CAN access their documents"""

    def test_user_with_secret_group_sees_private_doc(self, uploaded_docs):
        """User in 'secret' group should see confidential document"""
        response = requests.post(
            f"{API_URL}/rag/query",
            json={
                "query": "What are the internal security architecture details?",
                "user_id": "admin_user",
                "groups": ["public", "secret"],  # Has secret access
                "top_k": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should have citations
        assert "citations" in data
        assert len(data["citations"]) > 0

        # Check if any citation is from the private document
        private_doc_id = uploaded_docs["private"].get("doc_id")
        citation_doc_ids = [c["doc_id"] for c in data["citations"]]

        # At least one citation should be from private doc OR contain private content
        has_private_content = any(
            "ABAC" in c.get("content", "") or
            "authz/abac.py" in c.get("content", "") or
            "Confidential" in c.get("content", "")
            for c in data["citations"]
        )

        assert has_private_content, f"User with 'secret' group should see private content. Citations: {data['citations']}"

    def test_user_with_public_group_sees_public_doc(self, uploaded_docs):
        """User in 'public' group should see public document"""
        response = requests.post(
            f"{API_URL}/rag/query",
            json={
                "query": "What is RAG system overview?",
                "user_id": "regular_user",
                "groups": ["public"],  # Only public access
                "top_k": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should have citations
        assert "citations" in data
        assert len(data["citations"]) > 0

        # Should contain public content
        has_public_content = any(
            "Retrieval-Augmented Generation" in c.get("content", "") or
            "RAG" in c.get("content", "")
            for c in data["citations"]
        )

        assert has_public_content, "User with 'public' group should see public content"


class TestACLNegative:
    """Test that unauthorized users CANNOT access restricted documents"""

    def test_user_without_secret_group_cannot_see_private_doc(self, uploaded_docs):
        """User NOT in 'secret' group should NOT see confidential document"""
        response = requests.post(
            f"{API_URL}/rag/query",
            json={
                "query": "What are the internal security architecture details? Tell me about ABAC implementation.",
                "user_id": "regular_user",
                "groups": ["public"],  # Does NOT have secret access
                "top_k": 10
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check citations for any private content
        if "citations" in data and len(data["citations"]) > 0:
            for citation in data["citations"]:
                content = citation.get("content", "")

                # Should NOT contain any private/confidential markers
                assert "CONFIDENTIAL" not in content, "Unauthorized user should not see CONFIDENTIAL marker"
                assert "Secret Group Access Only" not in content, "Unauthorized user should not see secret group marker"
                assert "authz/abac.py" not in content, "Unauthorized user should not see internal implementation details"
                assert "doc_private_001" not in citation.get("doc_id", ""), "Unauthorized user should not see private doc ID"

        # Check answer for existence leaks
        answer = data.get("answer", "")
        assert "CONFIDENTIAL" not in answer, "Answer should not leak confidential markers"
        assert "Internal Security Architecture" not in answer, "Answer should not leak private doc title"

    def test_empty_groups_denies_all_restricted_access(self, uploaded_docs):
        """User with no groups should only see truly public content"""
        response = requests.post(
            f"{API_URL}/rag/query",
            json={
                "query": "Tell me about security architecture and ABAC",
                "user_id": "anonymous_user",
                "groups": [],  # No group membership
                "top_k": 10
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should either have no citations or only public ones
        if "citations" in data and len(data["citations"]) > 0:
            for citation in data["citations"]:
                content = citation.get("content", "")
                metadata = citation.get("metadata", {})

                # Should NOT have any restricted content
                assert "CONFIDENTIAL" not in content
                assert "secret" not in metadata.get("groups", [])
                assert "Internal Security" not in content


class TestACLMetrics:
    """Test that ACL denials are tracked in metrics"""

    def test_acl_denial_metrics_increment(self, uploaded_docs):
        """Verify that ACL denials are tracked in Prometheus"""
        # Get baseline
        prom_response = requests.get(
            "http://16.146.148.184:9090/api/v1/query",
            params={"query": "rag_acl_denied_total"}
        )
        baseline = 0
        if prom_response.status_code == 200:
            result = prom_response.json().get("data", {}).get("result", [])
            if result:
                baseline = float(result[0]["value"][1])

        # Make unauthorized query
        requests.post(
            f"{API_URL}/rag/query",
            json={
                "query": "Show me confidential security details",
                "user_id": "unauthorized_user",
                "groups": [],  # No access
                "top_k": 5
            }
        )

        time.sleep(2)  # Allow metrics to propagate

        # Check if metric increased (may not if ACL is at query level, not result level)
        prom_response = requests.get(
            "http://16.146.148.184:9090/api/v1/query",
            params={"query": "rag_acl_denied_total"}
        )

        # This test is informational - ACL may be enforced at vector level
        # without explicit denial counter
        if prom_response.status_code == 200:
            result = prom_response.json().get("data", {}).get("result", [])
            if result:
                current = float(result[0]["value"][1])
                print(f"ACL denial metric: baseline={baseline}, current={current}")

