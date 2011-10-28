# -*- coding: utf-8 -*-
from synt.trainer import train
from synt.collector import collect, fetch
from synt.guesser import Guesser 
from synt.accuracy import test_accuracy
import sys, time

try:
    import argparse
except ImportError:
    raise

VERSION = '0.1.0'

def main():

    parser = argparse.ArgumentParser(description='Tool to interface with synt, provides a way to train, collect and guess from the command line.')

    subparsers = parser.add_subparsers(dest='parser')

    #Train Parser
    train_parser = subparsers.add_parser(
        'train', 
        help='Train a classifier.'
    )
    train_parser.add_argument(
        'db', 
        help="The name of the training database to use. They are stored/retreived from ~/.synt/"
    )
    train_parser.add_argument(
        'samples',
        type=int,
        help="The amount of samples to train on. Uses the samples.db",
    )
    train_parser.add_argument(
        '--classifier',
        default='naivebayes',
        choices=('naivebayes',),
        help="The classifier to use. See help for currently supported classifier.",
    )
    train_parser.add_argument(
        '--extractor',
        default='stopwords',
        choices=('words', 'stopwords', 'bestwords'),
        help="The feature extractor to use. By default this uses stopwords filtering.",
    )
    train_parser.add_argument(
        '--best_features',
        type=int,
        default=0,
        help="The amount of best words to use, or best features. This should be used in conjunction with bestwords extractor.",
    )
    train_parser.add_argument(
        '--purge',
        default='no',
        choices=('yes', 'no'),
        help="Yes to purge the redis database. By default no."
    ) 
    train_parser.add_argument(
        '--processes',
        default=4,
        help="Will utilize multiprocessing if available with this number of processes. By default 4."
    )
    train_parser.add_argument(
        '--redis_db',
        default=5, 
        type=int,
        help="The redis db to use. By default 5",
    )

    #Collect parser
    collect_parser = subparsers.add_parser(
        'collect',
        help='Collect samples.'
    )
    collect_parser.add_argument(
        '--db',
        default=None,
        help="Optional database name to store as.",
    )
    collect_parser.add_argument(
        '--commit_every',
        default=200,
        type=int,
        help="Write to sqlite database after every 'this number'. Default is 200",
    )
    collect_parser.add_argument(
        '--max_collect',
        default=2000000,
        type=int,
        help="The amount to stop collecting at. Default is 2 million",
    )

    #Fetch parser
    fetch_parser = subparsers.add_parser(
        'fetch', 
        help='Fetches premade sample database.'
    )
    fetch_parser.add_argument(
        '--db', 
        help="Fetches the default samples database from github and stores it as 'db' in ~/.synt/. Default db name is 'samples.db'.",
        default='samples.db',
    )

    #Guess parser
    guess_parser = subparsers.add_parser(
        'guess',
        help='Guess sentiment'
    )
    guess_parser.add_argument(
        'guess', 
        nargs='?',
        default=True,
        help="Starts the guess prompt.",
    )
    guess_parser.add_argument(
        '--text',
        default='',
        help="Given text, will guess the sentiment on it.",
    )
    guess_parser.add_argument(
        '--redis_db',
        default=5, 
        help="The redis database to use.",
    )

    #Accuracy parser
    accuracy_parser = subparsers.add_parser(
        'accuracy', 
        help="Test accuracy of classifier.",
    )
    accuracy_parser.add_argument(
        '--test_samples', 
        type=int,
        help="""The amount of samples to test on. By default this is figured out internally and ammounts to 25% 
        of the training sample count. You can override this.""",
        default=0,
    )
    accuracy_parser.add_argument(
        '--neutral_range',
        default=0.2,
        type=float,
        help="Neutral range to use. By default there isn't one.",
    )
    accuracy_parser.add_argument(
        '--offset',
        default=0,
        type=int,
        help="""By default the test samples are taken from the offset of the trained samples. i.e if 100 samples are trained and we
        are testing on 25 it will start from 100-125 to ensure the testing samples are new. You can override what offset to use 
        with this argument.""",
    )
    accuracy_parser.add_argument(
        '--redis_db',
        default=5,
        type=int,
        help="You can override the redis database used, by default its the same as the training db.",
    )

    args = parser.parse_args()

    if args.parser == 'train':
        print("Beginning train on {} database with {} samples.".format(args.db, args.samples))
        
        start = time.time()
        
        purge = False
        if args.purge == 'yes':
            purge = True

        train(
            db            = args.db,
            samples       = args.samples,
            classifier    = args.classifier,
            extractor     = args.extractor,
            best_features = args.best_features,
            processes     = args.processes,
            purge         = purge,
            redis_db      = args.redis_db, 
        )
        
        print("Finished training in {}.".format(time.time() - start))

    elif args.parser == 'collect':
        print("Beginning collecting {} samples to {}.".format(args.max_collect, args.db))
        
        start = time.time() 
        
        collect(
            db           = args.db,
            commit_every = args.commit_every,
            max_collect  = args.max_collect,
        )    
        
        print("Finished collecting samples in {} seconds.".format(time.time() - start))

    elif args.parser == 'fetch':
        print("Beginning fetch to '{}' database.".format(args.db)) 
        fetch(args.db)
        print("Finished fetch.")

    elif args.parser == 'guess':
        g = Guesser(redis_db=args.redis_db)
        
        if args.text:
            print("Guessed: ",  g.guess(args.text))
            sys.exit()

        print("Enter something to calculate the synt of it!")
        print("Press enter to quit.")
    
        while True:
            text = raw_input("synt> ")
            if not text:
                break    
            print('Guessed: {}'.format(g.guess(text)))
    
    elif args.parser == 'accuracy':
        print("Beginning accuracy test with neutral range {}.".format(args.neutral_range))
        
        start = time.time()
        
        n_accur, m_accur, classifier = test_accuracy(
            test_samples  = args.test_samples,
            neutral_range = args.neutral_range,
            offset        = args.offset,
            redis_db      = args.redis_db,
        )
        
        print("NLTK Accuracy: {}".format(n_accur))
        print("Manual Accuracy: {}".format(m_accur))
        
        classifier.show_most_informative_features(50)
        
        print("Finished testing in {} seconds.".format(time.time() - start))

if __name__ == '__main__':
    main()
