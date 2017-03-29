import math
from flask import*
from vs_index import*
from flask_paginate import Pagination
from collections import defaultdict

#this model is for retrieving documents given user query
#and for implementing user web interface

#a class for user query retrieval
class IR():

        def __init__(self):

                se = Serializer()
                self.postings = se.deSerialize('shelve/postings')
                self.tfidf = se.deSerialize('shelve/tfidf')
                
                self.parser = Parser()
                self.weight = TFIDF()
                
                data = getData('films_corpus.json')    
                self.corpus = data.getCorpus()

        #function for computing the intersection of lists
        def intersect(self, result_list):
                #sort the lists according to the length
                terms = sorted(result_list, key=len)
                result = terms[0]
                i = 1
                
                while i < len(terms) and result is not None:
                        result = self.helper(result, terms[i])
                        i += 1
                        
                return result

        #helper function for computing intersection of two list
        def helper(self, p1, p2):

                i = 0
                j = 0
                answer = []
                while i != len(p1) and j != len(p2):
                        if p1[i] == p2[j]:
                                answer.append(p1[i])
                                i += 1
                                j += 1
                        elif p1[i] < p2[j]:
                                i += 1
                        else:
                                j += 1

                return answer

        #calculating the cosine scores
        def cosineScores(self, query, pos_list):

                #cosine score
                scores = defaultdict(float)

                for word in query:
                        w = self.weight.tfidf(word, Counter(query), query)
                        for doc_id in pos_list:
                                scores[doc_id] += self.tfidf[doc_id][word]*w

                return sorted(scores.keys(), key=lambda k: scores[k], reverse=True), scores

        def search(self, query):

                #get the words of the query and the ignoring terms
                query_terms, ignore_terms = self.parser.parseQuery(query)
                
                keywords = []
                doc_list = []
                search_result = []
                unknown_terms = []

                #find the term in the postings list
                for term in query_terms:
                        if term in self.postings:
                                keywords.append(term)
                                #add the document id to the doc_list
                                #if this document contains the term
                                doc_list.append(self.postings[term])
                        else:
                                unknown_terms.append(term)
                               
                ignore = ', '.join(ignore_terms)
                unknown = ', '.join(unknown_terms)

                if unknown == []:
                        return search_result, ignore, unknown

                if keywords != []:
                        conjunct = self.intersect(doc_list)
                        docId, cosine = self.cosineScores(keywords, conjunct)
                        documents = docId if len(docId) <= 30 else docId[:30]
                        search_result = self.findDoc(documents, cosine)
        
                return search_result, ignore, unknown

        #retrive documents and their cosine score given a list of doc ID 
        def findDoc(self, search_result, cosine):

                result = []
                for docID in search_result:
                        #append the consine store to title of the document
                        self.corpus[str(docID)]['title'] += ' | ' + str(round(cosine[docID],2))
                        result.append(self.corpus[str(docID)])

                return result

#User web interface
app = Flask(__name__)

@app.route('/index', methods=['POST', 'GET'])
@app.route('/index/<int:page>')
def index():
        
        query = ""
        if request.method == 'POST': 
                query = request.form['form-search']
                #if the query is empty string then we stay at the same page
                if query == None or query == "":
                        return render_template('index.html')
                
                ir = IR()
                result, ignore, unknown_term = ir.search(query)

                page = request.args.get('page', 1, type=int)
                
                length_res = len(result) if result is not None else 0

                pagination = Pagination(page=page, total = length_res, search = False,
                        record_name = 'results', css_framework='bootstrap3', per_page = 10)

                return render_template('search_results.html', query = query, ignor = ignore, unknown = unknown_term,
                                       results = result, pagination=pagination, search = False)

        return render_template('index.html')

@app.route('/search_results', methods=['POST', 'GET'])
def search_results():
        
        query = ""
        if request.method == 'POST': 
                query = request.form['form-search']
                if query == None or query == "":
                        return render_template('index.html')
                
                ir = IR()
                result, ignore, unknown_term = ir.search(query)

                page = request.args.get('page', 1, type=int)
                
                length_res = len(result) if result is not None else 0

                pagination = Pagination(page=page, total = length_res, search = False,
                        record_name = 'results', css_framework='bootstrap3', per_page = 10)

                return render_template('search_results.html', query = query, ignor = ignore, unknown = unknown_term,
                                       results = result, pagination=pagination, search = False)
        return render_template('search_results.html')

@app.route("/page")
def page():
        title = request.args.get('title')
        language = request.args.get('language')
        director = request.args.get('director')
        runtime = request.args.get('runtime')
        categories = request.args.get('categories')
        starring = request.args.get('starring')
        country = request.args.get('country')
        text = request.args.get('text')
        return render_template('page.html', title = title, language = language,
                               director = director, runtime = runtime, starring = starring,
                               country = country, categories = categories, text=text)

if __name__ == "__main__":
        app.debug = True
        app.run()
