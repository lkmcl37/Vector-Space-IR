#-*- coding: UTF-8 -*-
import nltk
import json
import pickle
import math
from collections import Counter
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

#This class is for tokenization, normalization and stopword removal
class Parser():

        def __init__(self):       
                self.porter = PorterStemmer()
                self.stop_words = set(stopwords.words('english'))
                self.stop_words.update(['\n*', '&', '``', '\n', '/',
                                '.', '#', ',','"', "'", '?',
                                '!', ':', ';', '(', ')', '[', ']',
                                '{', '}'])

        #Function for parsing data of the film corpus
        def parseData(self, data):
                
                term = set()
                result = {}
               
                for key, value in data.iteritems():
                        token = nltk.word_tokenize(value)
                        normalized = [self.porter.stem(i.lower()) for i in token if i.lower() not in self.stop_words]
                        term = set(term).union(set(normalized))
                        result[key] = normalized

                return result, term

        #Function for paring user query
        def parseQuery(self, query):

                tokens = nltk.word_tokenize(query)
                ignore_term = [i.lower() for i in tokens if i.lower() in self.stop_words]
                normalized = [self.porter.stem(i.lower()) for i in tokens if i.lower() not in self.stop_words]

                return normalized, ignore_term

#class for obtaining corpus from json file
class getData():

        def __init__(self, path): 
                self.ps = Parser()
                self.path = path

        #functions for obtaining data from json file
        def getCorpus(self):
                
                with open(self.path) as data_file:
                        data = json.load(data_file)

                return data

        def getField(self):
                
           data = self.getCorpus()
           fields = {}
           for i in range(1, 2041):
                fields[i] = data[str(i)]["title"] + ' ' + data[str(i)]["text"]
                
           return fields

#class for creating postings list and tfidf
class Postings():

        def __init__(self, path):
            self.weight = TFIDF()

            data = getData(path)

            parser = Parser()
            self.corpus = data.getField()
            self.fields, self.terms = parser.parseData(self.corpus)
        
        def buildPostings(self):

            countlist = []
            for doc in self.fields.values():
                countlist.append(Counter(doc))

        
            tfidf = {} #tfidf = {docID : {word : tfidf}}
            length = {} #length = {docID : document length}
            postings = {} #postings = {term : [docID1, docID2..]}
            terms_dict = []

            #Build postings list and normalized if/idf for each term
            for key, value in self.fields.iteritems():
                normal = 0.0
                dic = {}
                for word in value:
                        dic[word] = self.weight.tfidf(word, Counter(value), countlist)
                        #'normal' is the parameter used for length normalization later
                        normal += math.pow(dic[word], 2)
                for term in self.terms:
                        if term in value:
                                postings.setdefault(term,[]).append(key)
                #length of the document
                length[key] = math.sqrt(normal)
                #normalize the tfidf
                for word in dic.keys():
                        dic[word] = dic[word]/length[key]
                tfidf[key] = dic

            return postings, list(set(terms_dict)), tfidf

#class for creating unnormalized tfidf
class TFIDF():
        
        #helper functions for getting tf/idf
        def total_freq(self, term, count_list):
            #calculate the number of documents that contain term t
            total =  sum(1 for count in count_list if term in count)
            return total

        def tf(self, term, count):
            #TF(t) = Number of times term t appears in a document/Total number of terms in the document
            return float(count[term]) / sum(count.values())

        def idf(self, term, count_list):
            #IDF(t) = Total number of documents / Number of documents with term t in it
            return 1.0 +math.log(float(len(count_list)) / self.total_freq(term, count_list))

        def tfidf(self, term, count, count_list):
            return self.tf(term, count) * self.idf(term, count_list)

#class for creating serizalized files
class Serializer():
        
    def deSerialize(self, name):
        with open (name, 'rb') as fp:
            itemlist = pickle.load(fp)
        return itemlist

    def serialize(self, file, name):
        with open(name, 'wb') as fp:
            pickle.dump(file, fp)

def serialization():

        test = Postings('films_corpus.json')
        postings, terms, tfidf = test.buildPostings()
        se = Serializer()
        se.serialize(postings, 'postings')
        se.serialize(terms, 'terms')
        se.serialize(tfidf, 'tfidf')
        

if __name__ == '__main__':
        import time
        tStart = time.time()
        serialization()
        tEnd = time.time()
        print "It cost %f sec" % (tEnd - tStart)


