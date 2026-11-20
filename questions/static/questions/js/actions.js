const settings = document.querySelector('#ajax-controls');
const errorMessage = document.querySelector('#ajax-error');

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = !message;
}

async function submitAction(url, fields) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': settings.querySelector('[name="csrfmiddlewaretoken"]').value,
            'Accept': 'application/json',
        },
        body: new URLSearchParams(fields),
    });
    if (response.status === 401) {
        window.location.assign(settings.dataset.loginUrl);
        return null;
    }

    if (!(response.headers.get('Content-Type') || '').includes('application/json')) {
        throw new Error('Сервер не смог обработать запрос. Попробуйте ещё раз.');
    }
    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.error || 'Действие не выполнено.');
    }
    return result;
}

for (const widget of document.querySelectorAll('[data-vote-url]')) {
    const buttons = widget.querySelectorAll('button[data-value]');
    widget.addEventListener('click', async (event) => {
        const button = event.target.closest('button[data-value]');
        if (!button || button.disabled) return;

        showError('');
        buttons.forEach((control) => { control.disabled = true; });
        try {
            const result = await submitAction(widget.dataset.voteUrl, {
                target_id: widget.dataset.targetId,
                value: button.dataset.value,
            });
            if (!result) return;

            widget.querySelector('.rating__value').textContent = result.rating;
            buttons.forEach((control) => {
                const selected = Number(control.dataset.value) === result.vote;
                control.setAttribute('aria-pressed', String(selected));
                control.classList.toggle('is-liked', selected && result.vote === 1);
                control.classList.toggle('is-disliked', selected && result.vote === -1);
            });
        } catch (error) {
            showError(error.message || 'Действие не выполнено.');
        } finally {
            buttons.forEach((control) => {
                control.disabled = control.getAttribute('aria-pressed') === 'true';
            });
        }
    });
}

const answers = document.querySelectorAll('[data-correct-url]');
for (const input of answers) {
    input.addEventListener('change', async () => {
        const checked = input.checked;
        let result;
        showError('');
        answers.forEach((answer) => { answer.disabled = true; });
        try {
            result = await submitAction(input.dataset.correctUrl, {
                question_id: input.dataset.questionId,
                answer_id: input.dataset.answerId,
                is_correct: checked,
            });
            if (result) {
                answers.forEach((answer) => {
                    answer.checked = String(result.correct_answer_id) === answer.dataset.answerId;
                });
            }
        } catch (error) {
            showError(error.message || 'Действие не выполнено.');
        } finally {
            if (!result) input.checked = !checked;
            answers.forEach((answer) => { answer.disabled = false; });
        }
    });
}
