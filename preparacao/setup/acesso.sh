# Checagem de acesso ao GCP (use com: source setup/acesso.sh && checar_acesso)
# Sem acesso, mostra os comandos de autenticação e, num terminal interativo, oferece rodá-los.
checar_acesso() {
  if [[ -z "${GCP_PROJECT:-}" || "$GCP_PROJECT" == "SEU-PROJETO-GCP" ]]; then
    echo "✘ Defina o seu projeto em preparacao/.env.local:"
    echo "    GCP_PROJECT=\"<seu-projeto>\"   (copie o .env para .env.local e edite)"
    return 1
  fi
  _tem_acesso() {
    gcloud projects describe "$GCP_PROJECT" --format='value(projectId)' >/dev/null 2>&1 &&
      gcloud auth application-default print-access-token >/dev/null 2>&1
  }
  _tem_acesso && return 0

  local conta
  conta="$(gcloud config get-value account 2>/dev/null)"
  echo "✘ A conta atual do gcloud (${conta:-nenhuma}) não acessa o projeto $GCP_PROJECT, ou falta o login de aplicação."
  echo "  Autentique com a conta que tem acesso ao projeto:"
  echo "    gcloud auth login"
  echo "    gcloud auth application-default login"
  echo "    gcloud config set project $GCP_PROJECT"
  echo "    gcloud auth application-default set-quota-project $GCP_PROJECT"
  if [[ -t 0 ]]; then
    local ok
    read -r -p "Rodar esses comandos agora? [s/N] " ok
    if [[ "$ok" == "s" || "$ok" == "S" ]]; then
      gcloud auth login && gcloud auth application-default login &&
        gcloud config set project "$GCP_PROJECT" &&
        gcloud auth application-default set-quota-project "$GCP_PROJECT"
      _tem_acesso && { echo "✔ acesso ok"; return 0; }
    fi
  fi
  return 1
}
