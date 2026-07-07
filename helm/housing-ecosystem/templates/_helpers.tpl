{{- define "housing-ecosystem.apiName" -}}
{{ .Values.global.appName }}-api
{{- end }}

{{- define "housing-ecosystem.schedulerName" -}}
{{ .Values.global.appName }}-scheduler
{{- end }}

{{- define "housing-ecosystem.apiServiceName" -}}
{{ .Values.global.appName }}-api-service
{{- end }}
