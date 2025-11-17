import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Save, RefreshCw, Eye, AlertCircle, CheckCircle, FileText } from 'lucide-react';

interface PromptTemplate {
  name: string;
  description: string;
  template: string;
  variables: string[];
  updated_at: string;
  updated_by: string;
}

export function PromptsPage() {
  const [selectedPromptId, setSelectedPromptId] = useState<string>('rag_synthesis');
  const [editedTemplate, setEditedTemplate] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [previewResult, setPreviewResult] = useState<any>(null);
  const queryClient = useQueryClient();

  // Load all prompts
  const { data: prompts, isLoading } = useQuery({
    queryKey: ['prompts'],
    queryFn: () => api.getPrompts() as Promise<Record<string, PromptTemplate>>,
  });

  // Load selected prompt details
  const selectedPrompt = prompts?.[selectedPromptId];

  // Sync edited template when prompt changes
  useEffect(() => {
    if (selectedPrompt && !isEditing) {
      setEditedTemplate(selectedPrompt.template);
      setValidationResult(null);
      setPreviewResult(null);
    }
  }, [selectedPromptId, selectedPrompt, isEditing]);

  // Update prompt mutation
  const updateMutation = useMutation({
    mutationFn: ({ promptId, template }: { promptId: string; template: string }) =>
      api.updatePrompt(promptId, template),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      setIsEditing(false);
      setEditedTemplate('');
    },
  });

  // Validate prompt mutation
  const validateMutation = useMutation({
    mutationFn: ({ promptId, template }: { promptId: string; template: string }) =>
      api.validatePrompt(promptId, template),
    onSuccess: (data) => {
      setValidationResult(data);
    },
  });

  // Preview/render prompt mutation
  const previewMutation = useMutation({
    mutationFn: (promptId: string) => {
      // Use current template if editing, otherwise use saved template
      const templateToRender = isEditing ? editedTemplate : selectedPrompt?.template || '';

      // For preview, we need to call the render endpoint with the template
      // But the API expects to render the saved template, so we'll use the saved one
      return api.renderPrompt(promptId, {
        query: 'What is RAG?',
        source_context: ' The context includes 5 research articles from recent AI publications.',
        citation_instruction: 'Include citations [1], [2], etc.'
      });
    },
    onSuccess: (data) => {
      setPreviewResult(data);
    },
    onError: (error: any) => {
      setPreviewResult({
        error: error.message || 'Failed to render preview',
        variables: {},
        rendered: ''
      });
    },
  });

  const handleEdit = () => {
    setEditedTemplate(selectedPrompt?.template || '');
    setIsEditing(true);
    setValidationResult(null);
    setPreviewResult(null);
  };

  const handleSave = () => {
    updateMutation.mutate({
      promptId: selectedPromptId,
      template: editedTemplate,
    });
  };

  const handleValidate = () => {
    validateMutation.mutate({
      promptId: selectedPromptId,
      template: editedTemplate,
    });
  };

  const handlePreview = () => {
    previewMutation.mutate(selectedPromptId);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedTemplate('');
    setValidationResult(null);
    setPreviewResult(null);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  const currentTemplate = isEditing ? editedTemplate : selectedPrompt?.template || '';

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">System Prompts</h1>
        <p className="text-muted-foreground">
          Edit system prompts to control how the RAG system behaves. Changes take effect immediately without restarting services.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Prompt List Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Available Prompts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {prompts && Object.entries(prompts).map(([id, prompt]) => (
                <button
                  key={id}
                  onClick={() => {
                    setSelectedPromptId(id);
                    setIsEditing(false);
                    setValidationResult(null);
                    setPreviewResult(null);
                  }}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedPromptId === id
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <FileText className="h-5 w-5 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{prompt.name}</div>
                      <div className="text-xs opacity-75 mt-1 line-clamp-2">
                        {prompt.description}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Prompt Editor */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{selectedPrompt?.name}</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedPrompt?.description}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {!isEditing ? (
                    <>
                      <Button onClick={handlePreview} variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-2" />
                        Preview
                      </Button>
                      <Button onClick={handleEdit} size="sm">
                        Edit
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button onClick={handleCancel} variant="outline" size="sm">
                        Cancel
                      </Button>
                      <Button
                        onClick={handleValidate}
                        variant="outline"
                        size="sm"
                        disabled={validateMutation.isPending}
                      >
                        {validateMutation.isPending ? (
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <AlertCircle className="h-4 w-4 mr-2" />
                        )}
                        Validate
                      </Button>
                      <Button
                        onClick={handleSave}
                        size="sm"
                        disabled={updateMutation.isPending}
                      >
                        {updateMutation.isPending ? (
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4 mr-2" />
                        )}
                        Save
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Metadata */}
              <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Variables:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {selectedPrompt?.variables.map((v) => (
                      <code key={v} className="px-2 py-1 bg-muted rounded text-xs">
                        {`{${v}}`}
                      </code>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Last Updated:</span>
                  <div className="mt-1">
                    {new Date(selectedPrompt?.updated_at || '').toLocaleString()} by {selectedPrompt?.updated_by}
                  </div>
                </div>
              </div>

              {/* Template Editor */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Prompt Template</label>
                <textarea
                  value={currentTemplate}
                  onChange={(e) => setEditedTemplate(e.target.value)}
                  disabled={!isEditing}
                  className={`w-full h-64 p-3 border rounded-lg font-mono text-sm ${
                    isEditing
                      ? 'bg-background border-input'
                      : 'bg-muted border-muted cursor-not-allowed'
                  }`}
                  placeholder="Enter your prompt template here..."
                />
                <div className="text-xs text-muted-foreground">
                  {currentTemplate.length} characters
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Validation Results */}
          {validationResult && (
            <Card className={validationResult.valid ? 'border-green-500' : 'border-yellow-500'}>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  {validationResult.valid ? (
                    <>
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      Validation Passed
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-5 w-5 text-yellow-500" />
                      Validation Issues
                    </>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {validationResult.errors && validationResult.errors.length > 0 && (
                  <div>
                    <h4 className="font-medium text-red-600 mb-2">Errors:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {validationResult.errors.map((err: string, i: number) => (
                        <li key={i} className="text-sm text-red-600">{err}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {validationResult.warnings && validationResult.warnings.length > 0 && (
                  <div>
                    <h4 className="font-medium text-yellow-600 mb-2">Warnings:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {validationResult.warnings.map((warn: string, i: number) => (
                        <li key={i} className="text-sm text-yellow-600">{warn}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {validationResult.variables_found && validationResult.variables_found.length > 0 && (
                  <div className="text-sm text-muted-foreground">
                    Variables found: {validationResult.variables_found.map((v: string) => `{${v}}`).join(', ')}
                  </div>
                )}
                {validationResult.template_length !== undefined && (
                  <div className="text-sm text-muted-foreground">
                    Template length: {validationResult.template_length} characters
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Preview Results */}
          {previewResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Preview with Sample Data</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {previewResult.error ? (
                  <div className="text-red-600">
                    <AlertCircle className="h-5 w-5 inline mr-2" />
                    {previewResult.error}
                  </div>
                ) : (
                  <>
                    {previewResult.variables && (
                      <div>
                        <h4 className="font-medium mb-2 text-sm text-muted-foreground">Sample Variables:</h4>
                        <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
                          {JSON.stringify(previewResult.variables, null, 2)}
                        </pre>
                      </div>
                    )}
                    <div>
                      <h4 className="font-medium mb-2 text-sm text-muted-foreground">Rendered Output:</h4>
                      <div className="bg-muted p-4 rounded text-sm whitespace-pre-wrap font-mono">
                        {previewResult.rendered || previewResult.template || 'No preview available'}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Success Message */}
          {updateMutation.isSuccess && (
            <Card className="border-green-500">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  <span className="font-medium">
                    Prompt updated successfully! Changes are live immediately.
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error Message */}
          {updateMutation.isError && (
            <Card className="border-red-500">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-red-600">
                  <AlertCircle className="h-5 w-5" />
                  <span className="font-medium">
                    Failed to update prompt: {(updateMutation.error as any)?.message || 'Unknown error'}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

