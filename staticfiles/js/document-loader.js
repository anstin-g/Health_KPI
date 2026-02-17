document.addEventListener("DOMContentLoaded", function () {
    // Fetch documents from the server
    fetchDocuments();

    function fetchDocuments() {
        fetch("/dashboard/documents/")
        .then(response => response.json())
        .then(data => {
            console.log("Fetched Data:", data);

            if (!data.documents || data.documents.length === 0) {
              if(data.pending_documents && data.pending_documents.length != 0){
                  populatePendingDocuments(data.pending_documents);
                }
                handleNoDocuments();
                return;
            }

            populateFeaturedDocuments(data.documents.slice(0, 3));
            populatePendingDocuments(data.pending_documents);
            populateDocumentsTable(data.documents);
        })
        .catch(error => {
            console.error("Error fetching documents:", error);
            handleFetchError();
        });
    }

    function handleNoDocuments() {
        document.getElementById("featured-document-list").innerHTML = 
            '<div class="no-documents">No documents available at this time</div>';
        document.getElementById("table-body").innerHTML = 
            '<tr><td colspan="3" class="no-documents">No documents available at this time</td></tr>';
    }

    function handleFetchError() {
        document.getElementById("featured-document-list").innerHTML = 
            '<div class="no-documents">Error loading documents. Please try again later.</div>';
        document.getElementById("table-body").innerHTML = 
            '<tr><td colspan="3" class="no-documents">Error loading documents. Please try again later.</td></tr>';
    }

    function populateFeaturedDocuments(documents) {
        const featuredDocumentList = document.getElementById("featured-document-list");
        featuredDocumentList.innerHTML = "";

        documents.forEach(doc => {
            const card = document.createElement("div");
            card.classList.add("card");

            const fileName = document.createElement("h3");
            fileName.textContent = doc.file;
            fileName.setAttribute("title", doc.file);
            card.appendChild(fileName);

            const details = document.createElement("div");
            details.classList.add("details");
            for (const [key, value] of Object.entries(doc.details)) {
                const p = document.createElement("p");
                p.innerHTML = `<strong>${key}:</strong> ${value || "N/A"}`;
                details.appendChild(p);
            }

            card.appendChild(details);
            featuredDocumentList.appendChild(card);
        });
    }
    
    function populatePendingDocuments(documents) {
        openDocumentReviewPopup(documents);
    }

    async function pendingDocumentUpdate(selectedDocumentsList) {
        const documentReviewOverlay = document.getElementById('documentReviewOverlay');
        console.log(selectedDocumentsList);
        try {
            const response = await fetch("/dashboard/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    selected_documents: selectedDocumentsList
                })
            });

            if (!response.ok) {
                throw new Error("Failed to apply changes");
            }

            console.log("Changes applied successfully");
            documentReviewOverlay.style.display = "none";
            fetchDocuments();
        } catch (error) {
            console.error("Error applying changes:", error);
            alert("Failed to apply changes");
        }
    }


    function openDocumentReviewPopup(documents) {
        const documentCardContainer = document.getElementById('documentCardContainer');
        const documentReviewOverlay = document.getElementById('documentReviewOverlay');

        documentCardContainer.innerHTML = '';
        if (!Array.isArray(documents) || documents.length === 0) {
            documentReviewOverlay.style.display = 'none';
            return;
        }

        documents.forEach((doc) => {
            const docName = doc?.DocumentName ?? doc?.documentName;
            if (!docName) return;

            const card = document.createElement('div');
            card.className = 'document-card';

            const topRow = document.createElement('div');
            topRow.className = 'document-card-row document-card-top';

            const nameEl = document.createElement('div');
            nameEl.className = 'document-name';
            nameEl.textContent = docName;

            const buttonGroup = document.createElement('div');
            buttonGroup.className = 'document-card-buttons';

            const acceptButton = document.createElement('button');
            acceptButton.className = 'btn btn-accept accept-btn';
            acceptButton.textContent = 'Accept';
            acceptButton.type = 'button';
            acceptButton.addEventListener('click', (e) => {
                e.stopPropagation();
                doc['status'] = 'Accepted';
                pendingDocumentUpdate([doc]);
            });

            const discardButton = document.createElement('button');
            discardButton.className = 'btn btn-discard discard-btn';
            discardButton.textContent = 'Discard';
            discardButton.type = 'button';
            discardButton.addEventListener('click', (e) => {
                e.stopPropagation();
                doc['status'] = 'Discarded';
                pendingDocumentUpdate([doc]);
            });

            buttonGroup.appendChild(acceptButton);
            buttonGroup.appendChild(discardButton);
            topRow.appendChild(nameEl);
            topRow.appendChild(buttonGroup);

            const bottomRow = document.createElement('div');
            bottomRow.className = 'document-card-row document-card-bottom';

            const firstNameEl = document.createElement('div');
            firstNameEl.className = 'document-first-name';
            firstNameEl.innerHTML = `
                <span>First Name</span>
                <strong>${doc.FirstName}</strong>
            `;

            const extractedNameEl = document.createElement('div');
            extractedNameEl.className = 'document-extracted-name';
            extractedNameEl.innerHTML = `
                <span>Extracted Name</span>
                <strong>${doc.ExtractedName}</strong>
            `;

            bottomRow.appendChild(firstNameEl);
            bottomRow.appendChild(extractedNameEl);

            card.appendChild(topRow);
            card.appendChild(bottomRow);

            documentCardContainer.appendChild(card);
        });

        documentReviewOverlay.style.display = 'block';
    }

    function populateDocumentsTable(documents) {
        const tableBody = document.getElementById("table-body");
        tableBody.innerHTML = "";

        documents.forEach(doc => {
            const row = document.createElement("tr");

            const fileNameCell = document.createElement("td");
            fileNameCell.textContent = doc.file;
            fileNameCell.setAttribute("title", doc.file);
            row.appendChild(fileNameCell);

            const detailsCell = document.createElement("td");
            const detailsList = document.createElement("ul");
            detailsList.classList.add("details-list");

            for (const [key, value] of Object.entries(doc.details)) {
                const listItem = document.createElement("li");
                listItem.innerHTML = `<strong>${key}:</strong> ${value || "N/A"}`;
                detailsList.appendChild(listItem);
            }

            detailsCell.appendChild(detailsList);
            row.appendChild(detailsCell);

            const actionCell = document.createElement("td");
            const viewReportBtn = document.createElement("a");
            viewReportBtn.href = `/showcase_report/?document_name=${encodeURIComponent(doc.file)}`;
            viewReportBtn.classList.add("view-report-btn");
            viewReportBtn.textContent = "View Report";
            actionCell.appendChild(viewReportBtn);
            row.appendChild(actionCell);

            tableBody.appendChild(row);
        });
    }
}); // end DOMContentLoaded

